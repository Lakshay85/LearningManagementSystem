import re
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

from app.rag.structure.types import (
    ElementType,
    HeaderLevel,
    DocumentElement,
    ElementMetadata,
    StructuredDocument,
    DEFAULT_PARSER_CONFIG
)
from app.rag.structure.element_detector import ElementDetector

class DocumentStructureParser:
    def __init__(self, config: dict = None):
        self.config = {**DEFAULT_PARSER_CONFIG, **(config or {})}

    async def parse(
        self,
        text: str,
        metadata: dict
    ) -> StructuredDocument:
        start_time = time.time()
        elements: List[DocumentElement] = []
        position = 0

        lines = text.split('\n')
        current_paragraph: List[str] = []
        current_section = ""
        current_subsection = ""
        parent_header = ""
        in_code_block = False
        code_block_content: List[str] = []
        code_language = ""
        in_table = False
        table_lines: List[str] = []
        list_buffer: List[dict] = []

        def flush_paragraph():
            nonlocal position
            if current_paragraph:
                content = '\n'.join(current_paragraph).strip()
                if content:
                    elements.append(self.create_paragraph_element(
                        content,
                        position,
                        metadata.get("page"),
                        current_section,
                        current_subsection,
                        parent_header
                    ))
                    position += 1
                current_paragraph.clear()

        def flush_list():
            nonlocal position
            if list_buffer:
                is_ordered = list_buffer[0]["isOrdered"]
                items = [item["content"] for item in list_buffer]
                elements.append(self.create_list_element(
                    items,
                    is_ordered,
                    position,
                    metadata.get("page"),
                    current_section,
                    parent_header
                ))
                position += 1
                list_buffer.clear()

        def flush_table():
            nonlocal position, in_table, table_lines
            if table_lines:
                table_element = self.parse_space_separated_table(
                    table_lines,
                    position,
                    metadata.get("page"),
                    current_section,
                    parent_header
                )
                if not table_element:
                    table_element = self.parse_table_lines(
                        table_lines,
                        position,
                        metadata.get("page"),
                        current_section,
                        parent_header
                    )
                if table_element:
                    elements.append(table_element)
                    position += 1
                table_lines = []
                in_table = False

        def flush_code_block():
            nonlocal position, in_code_block, code_block_content, code_language
            if code_block_content:
                content = '\n'.join(code_block_content)
                elements.append(self.create_code_block_element(
                    content,
                    code_language,
                    position,
                    metadata.get("page"),
                    current_section,
                    parent_header
                ))
                position += 1
                code_block_content = []
                code_language = ""
                in_code_block = False

        i = 0
        while i < len(lines):
            line = lines[i]
            next_line = lines[i + 1] if i < len(lines) - 1 else None
            prev_line = lines[i - 1] if i > 0 else None

            # Handle code blocks
            if line.startswith('```'):
                if in_code_block:
                    flush_code_block()
                else:
                    flush_paragraph()
                    flush_list()
                    in_code_block = True
                    code_language = line[3:].strip()
                i += 1
                continue

            if in_code_block:
                code_block_content.append(line)
                i += 1
                continue

            # Check for headers
            header_level = ElementDetector.detect_header_level(line)
            if header_level or ElementDetector.is_likely_header(line, prev_line, next_line):
                flush_paragraph()
                flush_list()
                flush_table()

                level = header_level or self.infer_header_level(line)
                header_content = re.sub(r"^#{1,6}\s*", "", line).strip()
                
                if level <= 2:
                    current_section = header_content
                    current_subsection = ""
                else:
                    current_subsection = header_content
                parent_header = header_content

                elements.append(self.create_header_element(
                    header_content,
                    level,
                    position,
                    metadata.get("page"),
                    current_section
                ))
                position += 1

                if next_line and re.match(r"^[=-]{3,}$", next_line.strip()):
                    i += 1
                i += 1
                continue

            # Check for table rows
            if self.config.get("extractTables"):
                is_table_line = self.is_table_line(line, lines, i)
                if is_table_line:
                    flush_paragraph()
                    flush_list()
                    
                    if not in_table:
                        in_table = True
                    table_lines.append(line)
                    
                    if not next_line or not self.is_table_line(next_line, lines, i + 1):
                        flush_table()
                    i += 1
                    continue
                elif in_table:
                    flush_table()

            # Check for list items
            if self.config.get("extractLists"):
                is_item, is_ordered, item_content = ElementDetector.is_list_item(line)
                if is_item:
                    flush_paragraph()
                    flush_table()
                    
                    nesting_level = ElementDetector.get_list_nesting_level(line)
                    
                    if list_buffer and list_buffer[0]["isOrdered"] != is_ordered:
                        flush_list()
                        
                    list_buffer.append({
                        "content": item_content,
                        "isOrdered": is_ordered,
                        "level": nesting_level
                    })
                    i += 1
                    continue
                elif list_buffer:
                    flush_list()

            # Empty line -> flush paragraph
            if line.strip() == "":
                flush_paragraph()
                i += 1
                continue

            # Paragraph content
            current_paragraph.append(line)
            i += 1

        flush_paragraph()
        flush_list()
        flush_table()
        flush_code_block()

        hierarchy = self.build_hierarchy(elements)
        element_counts = self.count_elements(elements)

        return StructuredDocument(
            id=metadata["docId"],
            fileName=metadata["fileName"],
            docType=metadata["docType"],
            elements=elements,
            hierarchy=hierarchy,
            metadata={
                "totalPages": metadata.get("page"),
                "totalElements": len(elements),
                "elementCounts": element_counts,
                "extractionDate": datetime.now().isoformat(),
                "processingTime": int((time.time() - start_time) * 1000)
            }
        )

    def create_paragraph_element(
        self,
        content: str,
        position: int,
        page: Optional[int],
        section: str,
        subsection: str,
        parent_header: str
    ) -> DocumentElement:
        meta = ElementMetadata(
            section=section or None,
            subsection=subsection or None,
            parentHeader=parent_header or None
        )
        return DocumentElement(
            id=ElementDetector.generate_element_id(),
            type=ElementType.PARAGRAPH,
            content=content,
            page=page,
            position=position,
            metadata=meta
        )

    def create_header_element(
        self,
        content: str,
        level: HeaderLevel,
        position: int,
        page: Optional[int],
        section: str
    ) -> DocumentElement:
        meta = ElementMetadata(
            headerLevel=level,
            section=section or None
        )
        return DocumentElement(
            id=ElementDetector.generate_element_id(),
            type=ElementType.HEADER,
            content=content,
            page=page,
            position=position,
            metadata=meta
        )

    def create_list_element(
        self,
        items: List[str],
        is_ordered: bool,
        position: int,
        page: Optional[int],
        section: str,
        parent_header: str
    ) -> DocumentElement:
        lines = []
        for index, item in enumerate(items):
            prefix = f"{index + 1}. " if is_ordered else "• "
            lines.append(f"{prefix}{item}")
        content = '\n'.join(lines)

        meta = ElementMetadata(
            listType="ordered" if is_ordered else "unordered",
            listItems=items,
            section=section or None,
            parentHeader=parent_header or None
        )
        return DocumentElement(
            id=ElementDetector.generate_element_id(),
            type=ElementType.LIST,
            content=content,
            page=page,
            position=position,
            metadata=meta
        )

    def create_code_block_element(
        self,
        content: str,
        language: str,
        position: int,
        page: Optional[int],
        section: str,
        parent_header: str
    ) -> DocumentElement:
        meta = ElementMetadata(
            codeLanguage=language or None,
            section=section or None,
            parentHeader=parent_header or None
        )
        return DocumentElement(
            id=ElementDetector.generate_element_id(),
            type=ElementType.CODE_BLOCK,
            content=content,
            page=page,
            position=position,
            metadata=meta
        )

    def parse_table_lines(
        self,
        lines: List[str],
        position: int,
        page: Optional[int],
        section: str,
        parent_header: str
    ) -> Optional[DocumentElement]:
        if len(lines) < 2:
            return None

        data_lines = [l for l in lines if not re.match(r"^[\s|:-]+$", l.strip())]
        if not data_lines:
            return None

        def parse_row(line_str: str) -> List[str]:
            return [cell.strip() for cell in line_str.split('|') if cell.strip() != ""]

        headers = parse_row(data_lines[0])
        rows = [parse_row(l) for l in data_lines[1:]]

        content = self.format_table_as_text(headers, rows)

        meta = ElementMetadata(
            tableColumns=headers,
            tableRowCount=len(rows),
            section=section or None,
            parentHeader=parent_header or None
        )
        return DocumentElement(
            id=ElementDetector.generate_element_id(),
            type=ElementType.TABLE,
            content=content,
            rawContent='\n'.join(lines),
            page=page,
            position=position,
            metadata=meta
        )

    def format_table_as_text(self, headers: List[str], rows: List[List[str]]) -> str:
        header_line = f"Columns: {', '.join(headers)}"
        row_lines = []
        for index, row in enumerate(rows):
            cells = []
            for j, cell in enumerate(row):
                header_name = headers[j] if j < len(headers) else f"Col{j}"
                cells.append(f"{header_name}: {cell}")
            row_lines.append(f"Row {index + 1}: {'; '.join(cells)}")
        return f"{header_line}\n{chr(10).join(row_lines)}"

    def infer_header_level(self, text: str) -> HeaderLevel:
        if text == text.upper():
            return HeaderLevel.H1
        if re.match(r"^\d+\.\s", text):
            return HeaderLevel.H2
        if re.match(r"^\d+\.\d+\s", text):
            return HeaderLevel.H3
        return HeaderLevel.H2

    def build_hierarchy(self, elements: List[DocumentElement]) -> dict:
        sections = []
        current_section = None
        current_subsection = None

        for element in elements:
            if element.type == ElementType.HEADER:
                level = element.metadata.headerLevel or HeaderLevel.H2
                
                if level <= 2:
                    current_section = {
                        "id": element.id,
                        "title": element.content,
                        "level": level,
                        "elements": [],
                        "subsections": []
                    }
                    sections.append(current_section)
                    current_subsection = None
                elif current_section:
                    current_subsection = {
                        "id": element.id,
                        "title": element.content,
                        "level": level,
                        "elements": [],
                        "subsections": []
                    }
                    current_section["subsections"].append(current_subsection)
            else:
                if current_subsection:
                    current_subsection["elements"].append(element.to_dict())
                elif current_section:
                    current_section["elements"].append(element.to_dict())

        return {"sections": sections}

    def count_elements(self, elements: List[DocumentElement]) -> Dict[str, int]:
        counts = {el_type.value: 0 for el_type in ElementType}
        for element in elements:
            val = element.type.value if isinstance(element.type, ElementType) else element.type
            if val in counts:
                counts[val] += 1
        return counts

    def is_table_line(self, line: str, all_lines: List[str], current_index: int) -> bool:
        trimmed = line.strip()
        if not trimmed:
            return False

        if '|' in trimmed:
            return True

        if trimmed.count('\t') >= 2:
            return True

        multi_space = re.search(r"\S+\s{2,}\S+\s{2,}\S+", trimmed)
        if multi_space:
            prev_line = all_lines[current_index - 1].strip() if current_index > 0 else ""
            next_line = all_lines[current_index + 1].strip() if current_index < len(all_lines) - 1 else ""
            
            if prev_line and re.search(r"\S+\s{2,}\S+\s{2,}\S+", prev_line):
                return True
            if next_line and re.search(r"\S+\s{2,}\S+\s{2,}\S+", next_line):
                return True
            if next_line and re.match(r"^\d+\s+", next_line):
                return True

        if re.match(r"^\d+\s{2,}\w+", trimmed):
            return True

        segments = [s.strip() for s in re.split(r"\s{2,}", trimmed) if s.strip()]
        if len(segments) >= 3:
            def check_line(idx: int) -> bool:
                if idx < 0 or idx >= len(all_lines):
                    return False
                check_l = all_lines[idx].strip()
                if not check_l:
                    return False
                check_segs = [s.strip() for s in re.split(r"\s{2,}", check_l) if s.strip()]
                return abs(len(check_segs) - len(segments)) <= 1

            if check_line(current_index - 1) or check_line(current_index + 1):
                return True

        return False

    def parse_space_separated_table(
        self,
        lines: List[str],
        position: int,
        page: Optional[int],
        section: str,
        parent_header: str
    ) -> Optional[DocumentElement]:
        if len(lines) < 2:
            return None

        first_line = lines[0]
        if '|' in first_line:
            sep = r"\s*\|\s*"
        elif '\t' in first_line:
            sep = r"\t+"
        else:
            sep = r"\s{2,}"

        def parse_row(line_str: str) -> List[str]:
            if '|' in line_str:
                return [c.strip() for c in line_str.split('|') if c.strip() and not re.match(r"^[-:]+$", c.strip())]
            return [c.strip() for c in re.split(sep, line_str) if c.strip()]

        data_lines = []
        for l in lines:
            t = l.strip()
            if t and not re.match(r"^[\s|:-]+$", t) and not re.match(r"^[-=]+$", t):
                data_lines.append(l)

        if not data_lines:
            return None

        headers = parse_row(data_lines[0])
        rows = [parse_row(l) for l in data_lines[1:]]

        normalized_rows = []
        for row in rows:
            while len(row) < len(headers):
                row.append('')
            row = row[:len(headers)]
            if any(cell.strip() for cell in row):
                normalized_rows.append(row)

        content = self.format_table_as_text(headers, normalized_rows)

        meta = ElementMetadata(
            tableColumns=headers,
            tableRowCount=len(normalized_rows),
            section=section or None,
            parentHeader=parent_header or None
        )
        return DocumentElement(
            id=ElementDetector.generate_element_id(),
            type=ElementType.TABLE,
            content=content,
            rawContent='\n'.join(lines),
            page=page,
            position=position,
            metadata=meta
        )

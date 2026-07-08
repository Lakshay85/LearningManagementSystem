import re
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document

from app.rag.structure.types import (
    ElementType,
    HeaderLevel,
    DocumentElement,
    StructuredDocument,
    StructuredChunk
)
from app.rag.structure.element_detector import ElementDetector

class SmartChunkerConfig:
    def __init__(
        self,
        maxChunkSize: int = 1500,
        minChunkSize: int = 50,
        sentenceOverlap: int = 2,
        preserveTableIntegrity: bool = True,
        preserveListIntegrity: bool = True,
        attachHeadersToContent: bool = True
    ):
        self.maxChunkSize = maxChunkSize
        self.minChunkSize = minChunkSize
        self.sentenceOverlap = sentenceOverlap
        self.preserveTableIntegrity = preserveTableIntegrity
        self.preserveListIntegrity = preserveListIntegrity
        self.attachHeadersToContent = attachHeadersToContent

    def to_dict(self) -> dict:
        return self.__dict__

class SmartChunker:
    def __init__(self, config: dict = None):
        cfg = config or {}
        self.config = SmartChunkerConfig(
            maxChunkSize=cfg.get("maxChunkSize", 1500),
            minChunkSize=cfg.get("minChunkSize", 50),
            sentenceOverlap=cfg.get("sentenceOverlap", 2),
            preserveTableIntegrity=cfg.get("preserveTableIntegrity", True),
            preserveListIntegrity=cfg.get("preserveListIntegrity", True),
            attachHeadersToContent=cfg.get("attachHeadersToContent", True)
        )

    async def chunk_document(self, structured_doc: StructuredDocument) -> List[StructuredChunk]:
        chunks: List[StructuredChunk] = []
        chunk_index = 0
        current_header = ""

        for element in structured_doc.elements:
            element_chunks = await self.chunk_element(
                element,
                structured_doc,
                chunk_index,
                current_header
            )

            # Update current header context
            if element.type == ElementType.HEADER or element.type.value == "header":
                current_header = element.content

            for chunk in element_chunks:
                chunk.metadata["chunkIndex"] = chunk_index
                chunk_index += 1
                chunks.append(chunk)

        return chunks

    async def chunk_element(
        self,
        element: DocumentElement,
        doc: StructuredDocument,
        start_index: int,
        current_header: str
    ) -> List[StructuredChunk]:
        base_metadata = {
            "docId": doc.id,
            "docName": doc.fileName,
            "docType": doc.docType,
            "elementType": element.type.value if isinstance(element.type, ElementType) else element.type,
            "page": element.page,
            "section": element.metadata.section if hasattr(element.metadata, "section") else element.metadata.get("section"),
            "parentHeader": (element.metadata.parentHeader if hasattr(element.metadata, "parentHeader") else element.metadata.get("parentHeader")) or current_header,
            "subsection": element.metadata.subsection if hasattr(element.metadata, "subsection") else element.metadata.get("subsection"),
            "elementId": element.id,
            "position": element.position,
        }

        # Safe attribute access depending on if element is subclass or dict
        el_type = element.type.value if isinstance(element.type, ElementType) else element.type
        
        if el_type == ElementType.TABLE.value:
            # Table fields
            headers = getattr(element, "headers", element.metadata.tableColumns if hasattr(element.metadata, "tableColumns") else element.metadata.get("tableColumns") or [])
            rows = getattr(element, "rows", [])
            return self.chunk_table(element, headers, rows, base_metadata)
            
        elif el_type == ElementType.LIST.value:
            items = getattr(element, "items", element.metadata.listItems if hasattr(element.metadata, "listItems") else element.metadata.get("listItems") or [])
            is_ordered = getattr(element, "isOrdered", (element.metadata.listType if hasattr(element.metadata, "listType") else element.metadata.get("listType")) == "ordered")
            return self.chunk_list(element, items, is_ordered, base_metadata)
            
        elif el_type == ElementType.HEADER.value:
            return self.chunk_header(element, base_metadata)
            
        elif el_type == ElementType.CODE_BLOCK.value:
            return self.chunk_code_block(element, base_metadata)
            
        else: # PARAGRAPH and others
            return self.chunk_paragraph(element, base_metadata)

    def chunk_table(
        self,
        element: Any,
        headers: List[str],
        rows: List[List[str]],
        base_metadata: dict
    ) -> List[StructuredChunk]:
        chunks = []
        header_context = f"[Table with columns: {', '.join(headers)}]" if headers else "[Table]"
        parent_header = base_metadata.get("parentHeader")
        parent_context = f"Context: {parent_header}\n" if parent_header else ""

        full_content = f"{parent_context}{header_context}\n{element.content}"

        if len(full_content) <= self.config.maxChunkSize:
            chunks.append(StructuredChunk(
                id=ElementDetector.generate_element_id(),
                content=full_content,
                type=ElementType.TABLE,
                metadata={
                    **base_metadata,
                    "chunkIndex": 0,
                    "tableContext": header_context,
                    "hasNumericData": ElementDetector.contains_numeric_data(element.content),
                    "columnHeaders": headers,
                    "containsNumbers": True,
                }
            ))
        else:
            # Split table by rows
            row_chunks = self.split_table_by_rows(headers, rows, parent_context, header_context)
            for idx, r_chunk in enumerate(row_chunks):
                chunks.append(StructuredChunk(
                    id=ElementDetector.generate_element_id(),
                    content=r_chunk,
                    type=ElementType.TABLE,
                    metadata={
                        **base_metadata,
                        "chunkIndex": idx,
                        "tableContext": header_context,
                        "hasNumericData": ElementDetector.contains_numeric_data(r_chunk),
                        "columnHeaders": headers,
                        "containsNumbers": True,
                    }
                ))
        return chunks

    def split_table_by_rows(
        self,
        headers: List[str],
        rows: List[List[str]],
        parent_context: str,
        header_context: str
    ) -> List[str]:
        chunks = []
        prefix = f"{parent_context}{header_context}\n"
        current_chunk = prefix

        for row in rows:
            cells = []
            for i, cell in enumerate(row):
                header_name = headers[i] if i < len(headers) else f"Col{i}"
                cells.append(f"{header_name}: {cell}")
            row_line = f"{'; '.join(cells)}\n"

            if len(current_chunk) + len(row_line) > self.config.maxChunkSize:
                if current_chunk != prefix:
                    chunks.append(current_chunk.strip())
                current_chunk = prefix + row_line
            else:
                current_chunk += row_line

        if current_chunk != prefix:
            chunks.append(current_chunk.strip())
        return chunks

    def chunk_list(
        self,
        element: Any,
        items: List[str],
        is_ordered: bool,
        base_metadata: dict
    ) -> List[StructuredChunk]:
        chunks = []
        parent_header = base_metadata.get("parentHeader")
        context_prefix = f"{parent_header}:\n" if parent_header else ""

        full_content = context_prefix + element.content

        if len(full_content) <= self.config.maxChunkSize:
            chunks.append(StructuredChunk(
                id=ElementDetector.generate_element_id(),
                content=full_content,
                type=ElementType.LIST,
                metadata={
                    **base_metadata,
                    "chunkIndex": 0,
                    "listType": "ordered" if is_ordered else "unordered",
                    "listItemCount": len(items),
                }
            ))
        else:
            item_groups = self.group_list_items(items)
            for idx, group in enumerate(item_groups):
                group_lines = []
                for i, item in enumerate(group):
                    prefix = f"{i + 1}. " if is_ordered else "• "
                    group_lines.append(f"{prefix}{item}")
                content = context_prefix + '\n'.join(group_lines)
                
                chunks.append(StructuredChunk(
                    id=ElementDetector.generate_element_id(),
                    content=content,
                    type=ElementType.LIST,
                    metadata={
                        **base_metadata,
                        "chunkIndex": idx,
                        "listType": "ordered" if is_ordered else "unordered",
                        "listItemCount": len(group),
                    }
                ))
        return chunks

    def group_list_items(self, items: List[str]) -> List[List[str]]:
        groups = []
        current_group = []
        current_length = 0

        for item in items:
            if current_length + len(item) > self.config.maxChunkSize - 100:
                if current_group:
                    groups.append(current_group)
                current_group = [item]
                current_length = len(item)
            else:
                current_group.append(item)
                current_length += len(item) + 3
        
        if current_group:
            groups.append(current_group)
        return groups

    def chunk_header(self, element: Any, base_metadata: dict) -> List[StructuredChunk]:
        return [StructuredChunk(
            id=ElementDetector.generate_element_id(),
            content=element.content,
            type=ElementType.HEADER,
            metadata={
                **base_metadata,
                "chunkIndex": 0,
            }
        )]

    def chunk_code_block(self, element: Any, base_metadata: dict) -> List[StructuredChunk]:
        chunks = []
        language = (element.metadata.codeLanguage if hasattr(element.metadata, "codeLanguage") else element.metadata.get("codeLanguage")) or "code"
        parent_header = base_metadata.get("parentHeader")
        context_prefix = f"{parent_header} ({language}):\n" if parent_header else f"[{language}]:\n"

        full_content = context_prefix + element.content

        if len(full_content) <= self.config.maxChunkSize:
            chunks.append(StructuredChunk(
                id=ElementDetector.generate_element_id(),
                content=full_content,
                type=ElementType.CODE_BLOCK,
                metadata={
                    **base_metadata,
                    "chunkIndex": 0,
                    "codeLanguage": language,
                }
            ))
        else:
            code_chunks = self.split_code_block(element.content)
            for idx, c_chunk in enumerate(code_chunks):
                chunks.append(StructuredChunk(
                    id=ElementDetector.generate_element_id(),
                    content=context_prefix + c_chunk,
                    type=ElementType.CODE_BLOCK,
                    metadata={
                        **base_metadata,
                        "chunkIndex": idx,
                        "codeLanguage": language,
                    }
                ))
        return chunks

    def split_code_block(self, code: str) -> List[str]:
        lines = code.split('\n')
        chunks = []
        current_chunk = []
        current_length = 0

        for line in lines:
            is_boundary = any(line.strip().startswith(kw) for kw in ["function ", "class ", "def ", "async def ", "export "])
            
            if is_boundary and current_length > self.config.minChunkSize:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_length = len(line)
            elif current_length + len(line) > self.config.maxChunkSize:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_length = len(line)
            else:
                current_chunk.append(line)
                current_length += len(line) + 1

        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        return chunks

    def chunk_paragraph(self, element: Any, base_metadata: dict) -> List[StructuredChunk]:
        chunks = []
        text = element.content

        if len(text) <= self.config.maxChunkSize:
            chunks.append(StructuredChunk(
                id=ElementDetector.generate_element_id(),
                content=self.add_context_to_chunk(text, base_metadata),
                type=ElementType.PARAGRAPH,
                metadata={
                    **base_metadata,
                    "chunkIndex": 0,
                    "containsNumbers": ElementDetector.contains_numeric_data(text),
                    "containsDates": ElementDetector.contains_dates(text),
                }
            ))
            return chunks

        sentences = self.split_into_sentences(text)
        sentence_groups = self.group_sentences(sentences)

        for idx, s_group in enumerate(sentence_groups):
            content = ' '.join(s_group)
            chunks.append(StructuredChunk(
                id=ElementDetector.generate_element_id(),
                content=self.add_context_to_chunk(content, base_metadata),
                type=ElementType.PARAGRAPH,
                metadata={
                    **base_metadata,
                    "chunkIndex": idx,
                    "containsNumbers": ElementDetector.contains_numeric_data(content),
                    "containsDates": ElementDetector.contains_dates(content),
                }
            ))
        return chunks

    def split_into_sentences(self, text: str) -> List[str]:
        # Split on sentence endings but preserve decimals and abbreviations
        # In Python, we can match: [^.!?]*[.!?]+(?:\s|$)
        sentence_regex = r"[^.!?]*[.!?]+(?:\s|$)|[^.!?]+$"
        matches = re.findall(sentence_regex, text)
        return [s.strip() for s in matches if s.strip()]

    def group_sentences(self, sentences: List[str]) -> List[List[str]]:
        groups = []
        current_group = []
        current_length = 0

        for sentence in sentences:
            if current_length + len(sentence) > self.config.maxChunkSize and current_group:
                groups.append(list(current_group))
                overlap = current_group[-self.config.sentenceOverlap:] if len(current_group) >= self.config.sentenceOverlap else current_group
                current_group = list(overlap)
                current_length = sum(len(s) for s in overlap)
            
            current_group.append(sentence)
            current_length += len(sentence) + 1

        if current_group:
            groups.append(current_group)
        return groups

    def add_context_to_chunk(self, content: str, metadata: dict) -> str:
        if not self.config.attachHeadersToContent or not metadata.get("parentHeader"):
            return content
        
        section = metadata.get("section")
        parent_header = metadata.get("parentHeader")
        
        sec = section if section != parent_header else None
        context_parts = [p for p in [sec, parent_header] if p]
        
        if not context_parts:
            return content
            
        return f"[{' > '.join(context_parts)}]\n{content}"

    def to_langchain_documents(self, chunks: List[StructuredChunk]) -> List[Document]:
        docs = []
        for chunk in chunks:
            if chunk.content and chunk.content.strip():
                el_type = chunk.type.value if isinstance(chunk.type, ElementType) else chunk.type
                docs.append(Document(
                    page_content=chunk.content.strip(),
                    metadata={
                        **chunk.metadata,
                        "elementType": el_type,
                        "chunkId": chunk.id
                    }
                ))
        return docs

import re
import uuid
from typing import List, Dict, Any, Tuple, Optional
from app.rag.structure.types import ElementType, HeaderLevel

class ElementDetector:
    HEADER_PATTERNS = [
        r"^#{1,6}\s+(.+)$",
        r"^(.+)\n[=]{3,}$",
        r"^(.+)\n[-]{3,}$"
    ]

    TABLE_PATTERNS = [
        r"^\|(.+)\|$",
        r"^[\t|,;].+[\t|,;]$"
    ]

    LIST_PATTERNS = {
        "unordered": r"^[\s]*[-*•]\s+(.+)$",
        "ordered": r"^[\s]*\d+[.)]\s+(.+)$"
    }

    CODE_BLOCK_PATTERN = r"```(\w*)\n([\s\S]*?)```"
    QUOTE_PATTERN = r"^>\s+(.+)$"
    FORMULA_PATTERN = r"\$\$[\s\S]+?\$\$|\$[^$]+\$"

    @staticmethod
    def detect_header_level(line: str) -> Optional[HeaderLevel]:
        match = re.match(r"^(#{1,6})\s", line)
        if match:
            return HeaderLevel(len(match.group(1)))
        return None

    @staticmethod
    def is_likely_header(text: str, prev_line: Optional[str] = None, next_line: Optional[str] = None) -> bool:
        trimmed = text.strip()
        
        # Too long for a header
        if len(trimmed) > 200:
            return False
            
        # Markdown header
        if re.match(r"^#{1,6}\s", trimmed):
            return True
            
        # Short line followed by separator
        if next_line and re.match(r"^[=-]{3,}$", next_line.strip()):
            return True
            
        # ALL CAPS short text
        if len(trimmed) < 100 and trimmed == trimmed.upper() and any(c.isupper() for c in trimmed):
            return True
            
        # Numbered section like "1.1 Introduction"
        if re.match(r"^\d+(\.\d+)*\s+[A-Z]", trimmed):
            return True
            
        return False

    @staticmethod
    def is_table(lines: List[str]) -> bool:
        if len(lines) < 2:
            return False
            
        # Check for markdown table format
        has_row_separator = any(re.match(r"^\|?[-:|\s]+\|?$", line.strip()) for line in lines)
        has_table_rows = sum(1 for line in lines if '|' in line) >= 2
        
        if has_row_separator and has_table_rows:
            return True
            
        # Check for consistent column structure (tab or comma separated)
        column_counts = []
        for line in lines:
            tab_count = line.count('\t')
            comma_count = line.count(',')
            column_counts.append(max(tab_count, comma_count))
            
        if len(column_counts) >= 2 and all(c == column_counts[0] and c >= 1 for c in column_counts):
            return True
            
        return False

    @staticmethod
    def is_list_item(text: str) -> Tuple[bool, bool, str]:
        unordered_match = re.match(r"^[\s]*[-*•]\s+(.+)$", text)
        if unordered_match:
            return True, False, unordered_match.group(1)
            
        ordered_match = re.match(r"^[\s]*\d+[.)]\s+(.+)$", text)
        if ordered_match:
            return True, True, ordered_match.group(1)
            
        return False, False, text

    @staticmethod
    def get_list_nesting_level(line: str) -> int:
        match = re.match(r"^(\s*)", line)
        leading_spaces = len(match.group(1)) if match else 0
        return leading_spaces // 2

    @staticmethod
    def is_code_block(text: str) -> Tuple[bool, Optional[str]]:
        match = re.match(r"^```(\w*)", text)
        if match:
            return True, match.group(1) or None
            
        # Indented code block (4 spaces)
        is_item, _, _ = ElementDetector.is_list_item(text)
        if re.match(r"^( {4}|\t)", text) and not is_item:
            return True, None
            
        return False, None

    @staticmethod
    def contains_numeric_data(text: str) -> bool:
        numbers = re.findall(r"\b\d+(?:[.,]\d+)?\b", text) or []
        words = text.split()
        if not words:
            return False
        return len(numbers) / len(words) > 0.3

    @staticmethod
    def contains_dates(text: str) -> bool:
        date_patterns = [
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}\b",
            r"\b\d{4}[/-]\d{2}[/-]\d{2}\b"
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in date_patterns)

    @staticmethod
    def generate_element_id() -> str:
        return f"elem_{str(uuid.uuid4())[:8]}"

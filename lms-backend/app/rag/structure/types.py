from enum import Enum
from typing import List, Dict, Any, Optional

class ElementType(str, Enum):
    HEADER = 'header'
    PARAGRAPH = 'paragraph'
    TABLE = 'table'
    LIST = 'list'
    CODE_BLOCK = 'code_block'
    IMAGE = 'image'
    QUOTE = 'quote'
    FORMULA = 'formula'

class HeaderLevel(int, Enum):
    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4
    H5 = 5
    H6 = 6

class ElementMetadata:
    def __init__(
        self,
        headerLevel: Optional[HeaderLevel] = None,
        parentHeader: Optional[str] = None,
        section: Optional[str] = None,
        subsection: Optional[str] = None,
        listType: Optional[str] = None,
        listItems: Optional[List[str]] = None,
        tableColumns: Optional[List[str]] = None,
        tableRowCount: Optional[int] = None,
        codeLanguage: Optional[str] = None,
        fontSize: Optional[float] = None,
        isBold: Optional[bool] = None,
        confidence: Optional[float] = None
    ):
        self.headerLevel = headerLevel
        self.parentHeader = parentHeader
        self.section = section
        self.subsection = subsection
        self.listType = listType
        self.listItems = listItems
        self.tableColumns = tableColumns
        self.tableRowCount = tableRowCount
        self.codeLanguage = codeLanguage
        self.fontSize = fontSize
        self.isBold = isBold
        self.confidence = confidence

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

class DocumentElement:
    def __init__(
        self,
        id: str,
        type: ElementType,
        content: str,
        rawContent: Optional[str] = None,
        page: Optional[int] = None,
        position: int = 0,
        metadata: Optional[ElementMetadata] = None
    ):
        self.id = id
        self.type = type
        self.content = content
        self.rawContent = rawContent
        self.page = page
        self.position = position
        self.metadata = metadata or ElementMetadata()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, ElementType) else self.type,
            "content": self.content,
            "rawContent": self.rawContent,
            "page": self.page,
            "position": self.position,
            "metadata": self.metadata.to_dict() if hasattr(self.metadata, "to_dict") else self.metadata
        }

class StructuredDocument:
    def __init__(
        self,
        id: str,
        fileName: str,
        docType: str,
        elements: List[DocumentElement],
        hierarchy: Dict[str, Any],
        metadata: Dict[str, Any]
    ):
        self.id = id
        self.fileName = fileName
        self.docType = docType
        self.elements = elements
        self.hierarchy = hierarchy
        self.metadata = metadata

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "fileName": self.fileName,
            "docType": self.docType,
            "elements": [el.to_dict() for el in self.elements],
            "hierarchy": self.hierarchy,
            "metadata": self.metadata
        }

class StructuredChunk:
    def __init__(
        self,
        id: str,
        content: str,
        type: ElementType,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ):
        self.id = id
        self.content = content
        self.type = type
        self.metadata = metadata
        self.embedding = embedding

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "type": self.type.value if isinstance(self.type, ElementType) else self.type,
            "metadata": self.metadata,
            "embedding": self.embedding
        }

DEFAULT_PARSER_CONFIG = {
    "preserveFormatting": True,
    "extractTables": True,
    "extractLists": True,
    "extractCodeBlocks": True,
    "minHeaderFontSize": 14,
    "detectHierarchy": True,
}

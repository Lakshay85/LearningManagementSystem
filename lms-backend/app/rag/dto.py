from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class IngestTextDto(BaseModel):
    content: str
    fileName: str
    metadata: Optional[Dict[str, Any]] = None

class QueryDto(BaseModel):
    query: str
    sessionId: Optional[str] = None
    topK: Optional[int] = Field(default=5, ge=1, le=20)
    filters: Optional[Dict[str, Any]] = None

class IngestVideoDto(BaseModel):
    transcript: str
    videoName: str
    videoUrl: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CreateSessionDto(BaseModel):
    courseId: Optional[str] = None
    title: Optional[str] = None
    documentIds: Optional[List[str]] = None

class UpdateSessionDto(BaseModel):
    title: str

class IngestDocumentDto:
    def __init__(self, content: str, fileName: str, docType: str, metadata: Optional[dict] = None):
        self.content = content
        self.fileName = fileName
        self.docType = docType
        self.metadata = metadata or {}

class IngestFileDto:
    def __init__(self, fileBuffer: bytes, fileName: str, docType: str, metadata: Optional[dict] = None):
        self.fileBuffer = fileBuffer
        self.fileName = fileName
        self.docType = docType
        self.metadata = metadata or {}

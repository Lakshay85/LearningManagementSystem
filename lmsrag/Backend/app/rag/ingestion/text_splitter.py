import os
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.config import settings

class TextSplitResult:
    def __init__(self, chunks: List[Document], total_chunks: int):
        self.chunks = chunks
        self.totalChunks = total_chunks

class TextSplitter:
    def __init__(self, config: dict = None):
        cfg = config or {}
        chunk_size = cfg.get("chunkSize") or int(os.getenv("CHUNK_SIZE", str(settings.CHUNK_SIZE)))
        chunk_overlap = cfg.get("chunkOverlap") or int(os.getenv("CHUNK_OVERLAP", str(settings.CHUNK_OVERLAP)))
        separators = cfg.get("separators") or ["\n\n", "\n", " ", ""]

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators
        )

    async def split_documents(self, documents: List[Document]) -> TextSplitResult:
        try:
            # RecursiveCharacterTextSplitter split_documents is synchronous in Python
            chunks = self.splitter.split_documents(documents)
            
            # Add chunk index to metadata
            enriched_chunks = []
            for index, chunk in enumerate(chunks):
                chunk.metadata["chunkIndex"] = index
                enriched_chunks.append(chunk)

            return TextSplitResult(
                chunks=enriched_chunks,
                total_chunks=len(enriched_chunks)
            )
        except Exception as e:
            raise Exception(f"Failed to split documents: {str(e)}")

    async def split_text(self, text: str, metadata: Dict[str, Any] = None) -> TextSplitResult:
        meta = metadata or {}
        try:
            chunks = self.splitter.split_text(text)
            documents = []
            for index, chunk in enumerate(chunks):
                doc_meta = {**meta, "chunkIndex": index}
                documents.append(
                    Document(page_content=chunk, metadata=doc_meta)
                )
            return TextSplitResult(
                chunks=documents,
                total_chunks=len(documents)
            )
        except Exception as e:
            raise Exception(f"Failed to split text: {str(e)}")

    @classmethod
    def create(cls, config: dict) -> 'TextSplitter':
        return cls(config)

    def get_config(self) -> dict:
        return {
            "chunkSize": self.splitter._chunk_size,
            "chunkOverlap": self.splitter._chunk_overlap,
            "separators": self.splitter._separators
        }

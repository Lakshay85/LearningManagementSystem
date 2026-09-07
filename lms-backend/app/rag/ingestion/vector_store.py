from typing import List, Any
from langchain_core.documents import Document

from app.rag.db_service import rag_db_service

class VectorSearchResult:
    def __init__(self, documents: List[Document], scores: List[float]):
        self.documents = documents
        self.scores = scores

class VectorStoreResult:
    def __init__(self, ids: List[str], collection_name: str):
        self.ids = ids
        self.collectionName = collection_name

class VectorStore:
    def __init__(self, config: dict = None):
        cfg = config or {}
        self.config = {
            "tableName": "rag_documents",
            "collectionName": "rag_collection",
            **cfg
        }
        self.db = rag_db_service

    async def initialize(self, embeddings: Any = None):
        pass

    async def add_documents(self, documents: List[Document]) -> VectorStoreResult:
        try:
            ids = []
            for doc in documents:
                embedding = doc.metadata.get("embedding")
                if not embedding:
                    raise ValueError("Document must have embedding in metadata")

                result_rows = await self.db.insert_document(
                    doc_id=doc.metadata.get("docId"),
                    doc_name=doc.metadata.get("docName") or doc.metadata.get("fileName", "untitled"),
                    doc_type=doc.metadata.get("docType", "document"),
                    chunk_index=doc.metadata.get("chunkIndex", 0),
                    content=doc.page_content,
                    embedding=embedding,
                    metadata=doc.metadata
                )

                if result_rows:
                    ids.append(str(result_rows[0]["id"]))

            return VectorStoreResult(
                ids=ids,
                collection_name=self.config["collectionName"]
            )
        except Exception as e:
            raise Exception(f"Failed to add documents to vector store: {str(e)}")

    async def similarity_search(self, query: str, k: int = 5, filter_dict: dict = None) -> VectorSearchResult:
        raise NotImplementedError("Use rag_db_service.similarity_search directly")

    async def delete_documents(self, ids: List[str]):
        for id_val in ids:
            try:
                await self.db.execute("DELETE FROM rag_documents WHERE id = %s", int(id_val))
            except ValueError:
                pass

    def get_database_service(self):
        return self.db

    @classmethod
    def create(cls, config: dict = None) -> 'VectorStore':
        return cls(config)

    async def close(self):
        pass

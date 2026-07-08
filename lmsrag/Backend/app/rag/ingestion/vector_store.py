from typing import List, Dict, Any
from langchain_core.documents import Document

from app.database.service import db_service

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
            "tableName": "documents",
            "collectionName": "rag_collection",
            **cfg
        }
        self.db = db_service

    async def initialize(self, embeddings: Any = None):
        pass

    async def add_documents(self, documents: List[Document]) -> VectorStoreResult:
        try:
            ids = []
            for doc in documents:
                embedding = doc.metadata.get("embedding")
                if not embedding:
                    raise ValueError("Document must have embedding in metadata")

                # Insert document into pgvector
                # signature of insert_document: 
                # insert_document(self, doc_id, doc_name, doc_type, chunk_index, content, embedding, metadata)
                result_rows = await self.db.insert_document(
                    doc_id=doc.metadata.get("docId"),
                    doc_name=doc.metadata.get("docName"),
                    doc_type=doc.metadata.get("docType"),
                    chunk_index=doc.metadata.get("chunkIndex"),
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
        # We delegate to db_service for similarity searching.
        # But this throws in TS code (delegate to database service for now)
        raise NotImplementedError("Use DatabaseService.similarity_search for now")

    async def delete_documents(self, ids: List[str]):
        # Convert IDs to ints if they are numeric
        numeric_ids = []
        for id_val in ids:
            try:
                numeric_ids.append(int(id_val))
            except ValueError:
                pass
        
        for id_val in numeric_ids:
            await self.db.execute("DELETE FROM documents WHERE id = $1", id_val)

    def get_database_service(self):
        return self.db

    @classmethod
    def create(cls, config: dict = None) -> 'VectorStore':
        return cls(config)

    async def close(self):
        # Pool is closed at application shutdown, so we don't close it individually here
        pass

import json
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from app.database import engine, AsyncSessionLocal

class RagDatabaseService:
    """
    Asynchronous database service for RAG vector similarity search, document chunk storage,
    and ingestion job status tracking using SQLAlchemy async sessions.
    """

    async def connect(self):
        pass

    async def close(self):
        pass

    async def query(self, sql_text: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text(sql_text), params or {})
            if result.returns_rows:
                columns = result.keys()
                rows = result.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            return []

    async def execute(self, sql_text: str, params: Optional[Dict[str, Any]] = None):
        async with AsyncSessionLocal() as session:
            await session.execute(text(sql_text), params or {})
            await session.commit()

    async def insert_document(
        self,
        doc_id: str,
        doc_name: str,
        doc_type: str,
        chunk_index: int,
        content: str,
        embedding: List[float],
        metadata: Dict[str, Any] = None
    ):
        query_sql = """
            INSERT INTO rag_documents (doc_id, doc_name, doc_type, chunk_index, content, embedding, metadata)
            VALUES (:doc_id, :doc_name, :doc_type, :chunk_index, :content, CAST(:embedding AS vector), CAST(:metadata AS jsonb))
            RETURNING id
        """
        embedding_str = f"[{','.join(map(str, embedding))}]"
        metadata_str = json.dumps(metadata or {})
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(query_sql),
                {
                    "doc_id": doc_id,
                    "doc_name": doc_name,
                    "doc_type": doc_type,
                    "chunk_index": chunk_index,
                    "content": content,
                    "embedding": embedding_str,
                    "metadata": metadata_str
                }
            )
            await session.commit()
            row = result.fetchone()
            return [{"id": row[0]}] if row else []

    async def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        if filter_dict:
            query_sql = """
                SELECT 
                    id, doc_id, doc_name, doc_type, chunk_index, content, metadata,
                    1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM rag_documents
                WHERE metadata @> CAST(:filter_meta AS jsonb)
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
            """
            params = {
                "embedding": embedding_str,
                "filter_meta": json.dumps(filter_dict),
                "limit": top_k
            }
        else:
            query_sql = """
                SELECT 
                    id, doc_id, doc_name, doc_type, chunk_index, content, metadata,
                    1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM rag_documents
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
            """
            params = {
                "embedding": embedding_str,
                "limit": top_k
            }
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(text(query_sql), params)
            rows = result.fetchall()
            columns = result.keys()
            
            results = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                results.append({
                    "id": row_dict["id"],
                    "doc_id": row_dict["doc_id"],
                    "doc_name": row_dict["doc_name"],
                    "doc_type": row_dict["doc_type"],
                    "chunk_index": row_dict["chunk_index"],
                    "content": row_dict["content"],
                    "metadata": json.loads(row_dict["metadata"]) if isinstance(row_dict["metadata"], str) else (row_dict["metadata"] or {}),
                    "similarity": float(row_dict["similarity"]) if row_dict["similarity"] is not None else 0.0
                })
            return results

    async def delete_document_by_doc_id(self, doc_id: str):
        query_sql = "DELETE FROM rag_documents WHERE doc_id = :doc_id"
        async with AsyncSessionLocal() as session:
            await session.execute(text(query_sql), {"doc_id": doc_id})
            await session.commit()

    async def create_ingestion_job(self, doc_id: str, doc_name: str, doc_type: str):
        query_sql = """
            INSERT INTO rag_ingestion_jobs (doc_id, doc_name, doc_type, status)
            VALUES (:doc_id, :doc_name, :doc_type, 'processing')
            ON CONFLICT (doc_id) DO UPDATE SET status = 'processing', created_at = CURRENT_TIMESTAMP
            RETURNING id
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(text(query_sql), {"doc_id": doc_id, "doc_name": doc_name, "doc_type": doc_type})
            await session.commit()
            row = result.fetchone()
            return [{"id": row[0]}] if row else []

    async def update_ingestion_job(
        self,
        doc_id: str,
        status: str,
        total_chunks: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        query_sql = """
            UPDATE rag_ingestion_jobs
            SET status = :status, 
                total_chunks = COALESCE(:total_chunks, total_chunks), 
                error_message = :error_message, 
                completed_at = CURRENT_TIMESTAMP
            WHERE doc_id = :doc_id
        """
        async with AsyncSessionLocal() as session:
            await session.execute(
                text(query_sql),
                {
                    "status": status,
                    "total_chunks": total_chunks,
                    "error_message": error_message,
                    "doc_id": doc_id
                }
            )
            await session.commit()

    async def get_ingestion_job(self, doc_id: str) -> Optional[Dict[str, Any]]:
        query_sql = "SELECT * FROM rag_ingestion_jobs WHERE doc_id = :doc_id"
        async with AsyncSessionLocal() as session:
            result = await session.execute(text(query_sql), {"doc_id": doc_id})
            row = result.fetchone()
            if not row:
                return None
            columns = result.keys()
            row_dict = dict(zip(columns, row))
            if "created_at" in row_dict and row_dict["created_at"]:
                row_dict["created_at"] = row_dict["created_at"].isoformat()
            if "completed_at" in row_dict and row_dict["completed_at"]:
                row_dict["completed_at"] = row_dict["completed_at"].isoformat()
            return row_dict

# Global database service instance for RAG
rag_db_service = RagDatabaseService()

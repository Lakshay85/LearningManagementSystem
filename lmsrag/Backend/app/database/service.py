import asyncpg
import json
from typing import List, Dict, Any, Optional
from app.config import settings

class DatabaseService:
    def __init__(self):
        self.pool = None

    async def connect(self):
        if not self.pool:
            # Parse connectionString or pass directly
            self.pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=2,
                max_size=20,
                timeout=30.0
            )
            print("🐘 Connected to RAG PostgreSQL Database Pool")

    async def close(self):
        if self.pool:
            await self.pool.close()
            self.pool = None
            print("Closed RAG PostgreSQL connection pool")

    async def query(self, text: str, *params):
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as connection:
            return await connection.fetch(text, *params)

    async def execute(self, text: str, *params):
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as connection:
            return await connection.execute(text, *params)

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
        query = """
            INSERT INTO documents (doc_id, doc_name, doc_type, chunk_index, content, embedding, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """
        # Format the embedding list as a vector string, e.g. '[0.1,0.2,...]'
        embedding_str = f"[{','.join(map(str, embedding))}]"
        metadata_str = json.dumps(metadata or {})
        
        return await self.query(
            query,
            doc_id,
            doc_name,
            doc_type,
            chunk_index,
            content,
            embedding_str,
            metadata_str
        )

    async def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        query = """
            SELECT 
                id, doc_id, doc_name, doc_type, chunk_index, content, metadata,
                1 - (embedding <=> $1::vector) AS similarity
            FROM documents
        """
        
        params = [embedding_str]
        
        if filter_dict:
            query += " WHERE metadata @> $2::jsonb"
            params.append(json.dumps(filter_dict))
            
        limit_param_index = len(params) + 1
        query += f" ORDER BY embedding <=> $1::vector LIMIT ${limit_param_index}"
        params.append(top_k)
        
        rows = await self.query(query, *params)
        
        # Format rows into list of dicts
        results = []
        for row in rows:
            results.append({
                "id": row["id"],
                "doc_id": row["doc_id"],
                "doc_name": row["doc_name"],
                "doc_type": row["doc_type"],
                "chunk_index": row["chunk_index"],
                "content": row["content"],
                "metadata": json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"],
                "similarity": row["similarity"]
            })
        return results

    async def delete_document_by_doc_id(self, doc_id: str):
        return await self.execute("DELETE FROM documents WHERE doc_id = $1", doc_id)

    async def create_ingestion_job(self, doc_id: str, doc_name: str, doc_type: str):
        query = """
            INSERT INTO ingestion_jobs (doc_id, doc_name, doc_type, status)
            VALUES ($1, $2, $3, 'processing')
            ON CONFLICT (doc_id) DO UPDATE SET status = 'processing', created_at = CURRENT_TIMESTAMP
            RETURNING id
        """
        return await self.query(query, doc_id, doc_name, doc_type)

    async def update_ingestion_job(
        self,
        doc_id: str,
        status: str,
        total_chunks: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        query = """
            UPDATE ingestion_jobs
            SET status = $2, 
                total_chunks = COALESCE($3, total_chunks), 
                error_message = $4, 
                completed_at = CURRENT_TIMESTAMP
            WHERE doc_id = $1
        """
        return await self.execute(query, doc_id, status, total_chunks, error_message)

    async def get_ingestion_job(self, doc_id: str) -> Optional[Dict[str, Any]]:
        rows = await self.query("SELECT * FROM ingestion_jobs WHERE doc_id = $1", doc_id)
        if not rows:
            return None
        row = rows[0]
        return dict(row)

# Global database service instance for RAG
db_service = DatabaseService()

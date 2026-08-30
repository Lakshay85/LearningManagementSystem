import os
import uuid
import time
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document

from app.config import settings
from app.rag.db_service import rag_db_service
from app.chat.service import chat_memory_service
from app.llm.providers import LLMProviderManager
from app.rag.ingestion.document_loader import DocumentLoader
from app.rag.ingestion.text_splitter import TextSplitter
from app.rag.ingestion.embedder import Embedder
from app.rag.ingestion.vector_store import VectorStore
from app.rag.ingestion.structured_pipeline import StructuredIngestionPipeline

from app.rag.dto import IngestDocumentDto, IngestFileDto

class RagService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            print("⚠️ GROQ_API_KEY is not set in settings")

        primary_config = {
            "provider": "groq",
            "apiKey": self.api_key,
            "model": settings.GROQ_MODEL or "qwen/qwen3.8-27b",
            "temperature": 0.4,
            "maxTokens": 2048
        }
        self.llm_manager = LLMProviderManager(primary_config)

        self.document_loader = DocumentLoader()
        self.text_splitter = TextSplitter()
        self.embedder = Embedder.create_from_env()
        self.vector_store = VectorStore.create()

        self.db = rag_db_service
        self.chat_memory = chat_memory_service

        self.use_structured_pipeline = os.getenv("USE_STRUCTURED_PIPELINE", "true").lower() != "false"
        self.structured_pipeline = StructuredIngestionPipeline({
            "enableEnrichment": True,
            "chunkerConfig": {
                "maxChunkSize": int(os.getenv("CHUNK_SIZE", "1500")),
                "minChunkSize": int(os.getenv("MIN_CHUNK_SIZE", "100")),
                "sentenceOverlap": int(os.getenv("SENTENCE_OVERLAP", "2"))
            }
        })
        print("🚀 RAG Service initialized")

    async def close(self):
        await self.db.close()
        await self.vector_store.close()

    async def ingest_document(self, dto: IngestDocumentDto) -> dict:
        doc_id = str(uuid.uuid4())
        print(f"INGESTION_STARTED: {dto.fileName} ({dto.docType})")

        try:
            await self.db.create_ingestion_job(doc_id, dto.fileName, dto.docType)

            if self.use_structured_pipeline:
                return await self.ingest_with_structured_pipeline(doc_id, dto)

            split_result = await self.text_splitter.split_text(dto.content, {
                "docId": doc_id,
                "docName": dto.fileName,
                "docType": dto.docType,
                **(dto.metadata or {})
            })

            print(f"📄 Split document into {split_result.totalChunks} chunks")
            embedding_result = await self.embedder.embed_documents(split_result.chunks)

            for idx in range(len(embedding_result.documents)):
                doc = embedding_result.documents[idx]
                emb = embedding_result.embeddings[idx]

                await self.db.insert_document(
                    doc_id=doc_id,
                    doc_name=dto.fileName,
                    doc_type=dto.docType,
                    chunk_index=idx,
                    content=doc.page_content,
                    embedding=emb,
                    metadata=doc.metadata
                )

            await self.db.update_ingestion_job(doc_id, 'completed', split_result.totalChunks)
            return {"docId": doc_id, "chunks": split_result.totalChunks}

        except Exception as e:
            await self.db.update_ingestion_job(doc_id, 'failed', 0, str(e))
            print(f"INGESTION_FAILED: {dto.fileName}, error: {str(e)}")
            raise e

    async def ingest_with_structured_pipeline(self, doc_id: str, dto: IngestDocumentDto) -> dict:
        print("📐 Using structure-aware ingestion pipeline")
        
        result = await self.structured_pipeline.process_text(dto.content, {
            "docId": doc_id,
            "fileName": dto.fileName,
            "docType": dto.docType,
            **(dto.metadata or {})
        })

        print(f"📐 Structure extraction: {result.stats.totalElements} elements")
        print(f"   Created {result.stats.totalChunks} chunks")

        embedding_result = await self.embedder.embed_documents(result.langchainDocuments)

        for idx in range(len(embedding_result.documents)):
            doc = embedding_result.documents[idx]
            emb = embedding_result.embeddings[idx]

            await self.db.insert_document(
                doc_id=doc_id,
                doc_name=dto.fileName,
                doc_type=dto.docType,
                chunk_index=idx,
                content=doc.page_content,
                embedding=emb,
                metadata=doc.metadata
            )

        await self.db.update_ingestion_job(doc_id, 'completed', result.stats.totalChunks)
        return {
            "docId": doc_id,
            "chunks": result.stats.totalChunks,
            "stats": result.stats.to_dict()
        }

    async def ingest_file(self, dto: IngestFileDto) -> dict:
        doc_id = str(uuid.uuid4())
        print(f"FILE_INGESTION_STARTED: {dto.fileName} ({dto.docType})")

        try:
            await self.db.create_ingestion_job(doc_id, dto.fileName, dto.docType)

            if self.use_structured_pipeline:
                return await self.ingest_file_with_structured_pipeline(doc_id, dto)

            if dto.docType == 'pdf':
                load_result = await self.document_loader.load_pdf(
                    dto.fileBuffer,
                    dto.fileName,
                    {"docId": doc_id, **(dto.metadata or {})}
                )
            else:
                content = dto.fileBuffer.decode('utf-8', errors='ignore')
                load_result = await self.document_loader.load_text(
                    content,
                    dto.fileName,
                    {"docId": doc_id, **(dto.metadata or {})}
                )

            split_result = await self.text_splitter.split_documents(load_result.documents)
            embedding_result = await self.embedder.embed_documents(split_result.chunks)

            for idx in range(len(embedding_result.documents)):
                doc = embedding_result.documents[idx]
                emb = embedding_result.embeddings[idx]

                await self.db.insert_document(
                    doc_id=doc_id,
                    doc_name=dto.fileName,
                    doc_type=dto.docType,
                    chunk_index=idx,
                    content=doc.page_content,
                    embedding=emb,
                    metadata=doc.metadata
                )

            await self.db.update_ingestion_job(doc_id, 'completed', split_result.totalChunks)
            return {
                "docId": doc_id,
                "chunks": split_result.totalChunks,
                "pages": load_result.metadata.get("totalPages") if load_result.metadata else None
            }

        except Exception as e:
            await self.db.update_ingestion_job(doc_id, 'failed', 0, str(e))
            print(f"FILE_INGESTION_FAILED: {dto.fileName}, error: {str(e)}")
            raise e

    async def ingest_file_with_structured_pipeline(self, doc_id: str, dto: IngestFileDto) -> dict:
        print("📐 Using structure-aware file ingestion pipeline")

        if dto.docType == 'pdf':
            result = await self.structured_pipeline.process_pdf(dto.fileBuffer, {
                "docId": doc_id,
                "fileName": dto.fileName,
                **(dto.metadata or {})
            })
        else:
            content = dto.fileBuffer.decode('utf-8', errors='ignore')
            result = await self.structured_pipeline.process_text(content, {
                "docId": doc_id,
                "fileName": dto.fileName,
                "docType": dto.docType,
                **(dto.metadata or {})
            })

        print(f"📐 Structure extraction: {result.stats.totalElements} elements")
        print(f"   Smart chunking: {result.stats.totalChunks} chunks")

        embedding_result = await self.embedder.embed_documents(result.langchainDocuments)

        for idx in range(len(embedding_result.documents)):
            doc = embedding_result.documents[idx]
            emb = embedding_result.embeddings[idx]

            if not emb:
                print(f"❌ Skipping chunk {idx + 1}: invalid embedding")
                continue
            if not doc.page_content or not doc.page_content.strip():
                print(f"❌ Skipping chunk {idx + 1}: empty content")
                continue

            await self.db.insert_document(
                doc_id=doc_id,
                doc_name=dto.fileName,
                doc_type=dto.docType,
                chunk_index=idx,
                content=doc.page_content,
                embedding=emb,
                metadata=doc.metadata
            )

        await self.db.update_ingestion_job(doc_id, 'completed', result.stats.totalChunks)
        
        total_pages = 0
        if hasattr(result, "structuredDocument") and result.structuredDocument:
            total_pages = result.structuredDocument.metadata.get("totalPages", 0)

        return {
            "docId": doc_id,
            "chunks": result.stats.totalChunks,
            "pages": total_pages,
            "stats": result.stats.to_dict()
        }

    async def delete_document(self, doc_id: str):
        await self.db.delete_document_by_doc_id(doc_id)
        print(f"🗑️ Deleted document: {doc_id}")

    async def get_ingestion_status(self, doc_id: str) -> Optional[dict]:
        return await self.db.get_ingestion_job(doc_id)

    async def health_check(self) -> dict:
        components = {
            "database": False,
            "embedder": False,
            "llm": False
        }

        try:
            await self.db.get_ingestion_job('health-check')
            components["database"] = True
        except Exception as e:
            print(f"Database health check failed: {str(e)}")

        try:
            await self.embedder.embed_query('health check')
            components["embedder"] = True
        except Exception as e:
            print(f"Embedder health check failed: {str(e)}")

        try:
            await self.llm_manager.generate('Say "OK" if you are working.')
            components["llm"] = True
        except Exception as e:
            print(f"LLM health check failed: {str(e)}")

        all_healthy = all(components.values())
        return {
            "status": "healthy" if all_healthy else "degraded",
            "components": components
        }

    async def get_stats(self) -> dict:
        return {
            "totalDocuments": 0,
            "totalChunks": 0,
            "documentsByType": {}
        }

    # ==================== Chat Session Delegates ====================

    async def create_chat_session(self, user_id: str, course_id: Optional[str] = None, title: Optional[str] = None, document_ids: Optional[List[str]] = None) -> dict:
        sess = await self.chat_memory.create_session(
            user_id=user_id,
            course_id=course_id,
            title=title,
            document_ids=document_ids
        )
        return sess.to_dict() if hasattr(sess, "to_dict") else sess

    async def get_user_chat_sessions(self, user_id: str, course_id: Optional[str] = None) -> List[dict]:
        if course_id:
            sessions = await self.chat_memory.get_course_sessions_for_user(user_id, course_id)
        else:
            sessions = await self.chat_memory.get_user_sessions(user_id)
        return [s.to_dict() if hasattr(s, "to_dict") else s for s in sessions]

    async def get_chat_session(self, session_id: str, user_id: str) -> Optional[dict]:
        session = await self.chat_memory.get_session(session_id)
        if session and session.userId != user_id:
            return None
        return session.to_dict() if hasattr(session, "to_dict") else session

    async def get_session_messages(self, session_id: str) -> List[dict]:
        messages = await self.chat_memory.get_session_messages(session_id)
        return [m.to_dict() if hasattr(m, "to_dict") else m for m in messages]

    async def update_chat_session_title(self, session_id: str, title: str) -> None:
        await self.chat_memory.update_session_title(session_id, title)

    async def delete_chat_session(self, session_id: str) -> None:
        await self.chat_memory.delete_session(session_id)

    async def validate_session_ownership(self, session_id: Optional[str], user_id: Optional[str]) -> Optional[str]:
        if not session_id:
            return None
        if not user_id:
            return session_id

        session = await self.chat_memory.get_session(session_id)
        if not session:
            return None

        if session.userId != user_id:
            print(f"🚫 Session ownership violation: user {user_id} tried to access session {session_id}")
            raise PermissionError("You do not have access to this chat session")

        return session_id

# Singleton service instance
rag_service = RagService()

import json
import uuid
import time
import os
import asyncio
from typing import List, Dict, Any, Optional

class IngestionStatus:
    QUEUED = 'queued'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    RETRYING = 'retrying'

class IngestionStage:
    QUEUED = 'queued'
    UPLOADING = 'uploading'
    PARSING = 'parsing'
    CHUNKING = 'chunking'
    EMBEDDING = 'embedding'
    STORING = 'storing'
    COMPLETE = 'complete'
    FAILED = 'failed'

STAGE_PROGRESS = {
    IngestionStage.QUEUED: 0,
    IngestionStage.UPLOADING: 10,
    IngestionStage.PARSING: 25,
    IngestionStage.CHUNKING: 45,
    IngestionStage.EMBEDDING: 65,
    IngestionStage.STORING: 85,
    IngestionStage.COMPLETE: 100,
    IngestionStage.FAILED: -1,
}

class IngestionQueueService:
    def __init__(self):
        self._status_store: Dict[str, dict] = {}
        self.is_enabled = False
        self.queue_name = 'in_memory'

    async def connect(self):
        self.is_enabled = True
        print("✅ Ingestion Queue initialized (In-memory status store)")

    async def disconnect(self):
        pass

    async def add_to_queue(self, data: dict) -> str:
        if not self.is_enabled:
            self.is_enabled = True

        task_id = str(uuid.uuid4())
        
        progress = {
            "taskId": task_id,
            "status": IngestionStatus.QUEUED,
            "stage": IngestionStage.QUEUED,
            "progress": 0,
            "message": "Document queued for processing",
            "createdAt": time.time(),
            "updatedAt": time.time()
        }
        await self.update_progress(task_id, progress)

        # Run background ingestion task in-process
        asyncio.create_task(self._run_ingestion(task_id, data))
        
        print(f"📥 Added ingestion job: {task_id} ({data.get('fileName')})")
        return task_id

    async def _run_ingestion(self, task_id: str, job_data: dict):
        print(f"Executing in-process job for task {task_id}: {job_data.get('fileName')}")

        from app.rag.service import rag_service, IngestFileDto

        async def update_progress_cb(stage: str, message: str):
            prog = STAGE_PROGRESS.get(stage, 0)
            await self.update_progress(task_id, {
                "status": IngestionStatus.PROCESSING,
                "stage": stage,
                "progress": prog,
                "message": message
            })

        file_path = job_data.get("filePath")
        try:
            if not file_path or not os.path.exists(file_path):
                raise ValueError(f"File not found on disk: {file_path}")

            doc_type = job_data.get("type")
            file_name = job_data.get("fileName")
            course_id = job_data.get("courseId")
            metadata = job_data.get("metadata") or {}

            await update_progress_cb(IngestionStage.PARSING, "Parsing document...")

            # Read file bytes
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            dto = IngestFileDto(
                fileBuffer=file_bytes,
                fileName=file_name,
                docType=doc_type,
                metadata={**metadata, "courseId": course_id}
            )

            # Ingest using RAG service
            result = await rag_service.ingest_file(dto)

            # Mark as complete
            await self.update_progress(task_id, {
                "status": IngestionStatus.COMPLETED,
                "stage": IngestionStage.COMPLETE,
                "progress": 100,
                "message": "Document ingested successfully",
                "result": result
            })

            # Clean up temp file
            if os.path.exists(file_path):
                os.remove(file_path)

            return result

        except Exception as e:
            print(f"❌ In-process job failed for task {task_id}: {str(e)}")
            await self.update_progress(task_id, {
                "status": IngestionStatus.FAILED,
                "stage": IngestionStage.FAILED,
                "progress": -1,
                "message": "Processing failed",
                "error": str(e)
            })
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

    async def get_status(self, task_id: str) -> Optional[dict]:
        return self._status_store.get(task_id)

    def is_queue_enabled(self) -> bool:
        return self.is_enabled

    async def update_progress(self, task_id: str, progress_data: dict) -> None:
        existing = await self.get_status(task_id) or {}
        updated = {
            **existing,
            **progress_data,
            "taskId": task_id,
            "updatedAt": time.time()
        }
        if "createdAt" not in updated:
            updated["createdAt"] = time.time()

        self._status_store[task_id] = updated

    async def get_queue_stats(self) -> dict:
        return {
            "waiting": 0,
            "active": 0,
            "completed": 0,
            "failed": 0
        }

# Global singleton service
ingestion_queue_service = IngestionQueueService()

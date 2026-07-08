import os
import time
from arq.connections import RedisSettings

from app.config import settings
from app.rag.service import rag_service, IngestFileDto
from app.queue.service import (
    ingestion_queue_service,
    IngestionStatus,
    IngestionStage,
    STAGE_PROGRESS
)

async def ingest_document_job(ctx, job_data: dict):
    task_id = job_data["taskId"]
    print(f"Executing arq job for task {task_id}: {job_data.get('fileName')}")

    # Ensure services are initialized (e.g. database pool)
    from app.database.service import db_service
    await db_service.connect()
    await ingestion_queue_service.connect()

    async def update_progress(stage: str, message: str):
        prog = STAGE_PROGRESS.get(stage, 0)
        await ingestion_queue_service.update_progress(task_id, {
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

        await update_progress(IngestionStage.PARSING, "Parsing document...")

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
        await ingestion_queue_service.update_progress(task_id, {
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
        print(f"❌ Worker job failed for task {task_id}: {str(e)}")
        await ingestion_queue_service.update_progress(task_id, {
            "status": IngestionStatus.FAILED,
            "stage": IngestionStage.FAILED,
            "progress": -1,
            "message": "Processing failed",
            "error": str(e)
        })
        # Clean up temp file on failure
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        raise e

class WorkerSettings:
    functions = [ingest_document_job]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)

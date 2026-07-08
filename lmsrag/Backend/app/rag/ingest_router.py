import os
import json
import uuid
import time
import asyncio
from fastapi import APIRouter, Request, Response, UploadFile, File, Form, Body, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any

from app.queue.service import ingestion_queue_service, IngestionStatus, IngestionStage

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

# Ensure uploads folder exists
UPLOADS_DIR = os.path.join(os.getcwd(), "uploads", "documents")
os.makedirs(UPLOADS_DIR, exist_ok=True)

def get_document_type(mime_type: str) -> str:
    if mime_type == 'application/pdf':
        return 'pdf'
    if mime_type and mime_type.startswith('text/'):
        return 'text'
    return 'document'

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    courseId: str = Form(...),
    title: Optional[str] = Form(None),
    chunkSize: Optional[str] = Form(None),
    chunkOverlap: Optional[str] = Form(None)
):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    if not courseId:
        raise HTTPException(status_code=400, detail="courseId is required")

    if not ingestion_queue_service.is_queue_enabled():
        raise HTTPException(status_code=503, detail="Async ingestion not available. Redis not configured.")

    # Validate file type
    allowed_mimes = [
        'application/pdf',
        'text/plain',
        'text/markdown',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/json',
        'text/csv',
    ]
    if file.content_type not in allowed_mimes:
        # Check extensions as fallback
        ext = file.filename.split('.')[-1].lower()
        if ext not in ["pdf", "txt", "md", "docx", "json", "csv"]:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    # Write file to disk
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{int(time.time())}-{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOADS_DIR, unique_filename)

    try:
        content_bytes = await file.read()
        with open(file_path, "wb") as f:
            f.write(content_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file to disk: {str(e)}")

    # Prepare job data
    job_data = {
        "type": get_document_type(file.content_type),
        "filePath": file_path,
        "fileName": file.filename,
        "courseId": courseId,
        "userId": "system",
        "metadata": {
            "title": title or file.filename,
            "chunkSize": int(chunkSize) if chunkSize else int(os.getenv("CHUNK_SIZE", "1000")),
            "chunkOverlap": int(chunkOverlap) if chunkOverlap else int(os.getenv("CHUNK_OVERLAP", "200")),
            "mimeType": file.content_type,
            "uploadedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    }

    try:
        task_id = await ingestion_queue_service.add_to_queue(job_data)
        return {
            "taskId": task_id,
            "status": "queued",
            "message": f"Document \"{file.filename}\" queued for ingestion"
        }
    except Exception as e:
        # Cleanup file on failure
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{taskId}")
async def get_status(taskId: str):
    status_data = await ingestion_queue_service.get_status(taskId)
    if not status_data:
        raise HTTPException(status_code=404, detail="Job not found")
    return status_data

@router.get("/progress/{taskId}")
async def stream_progress(taskId: str):
    async def progress_generator():
        completed = False
        while not completed:
            status_data = await ingestion_queue_service.get_status(taskId)
            if not status_data:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break

            status_val = status_data.get("status")
            yield f"data: {json.dumps(status_data)}\n\n"

            if status_val in [IngestionStatus.COMPLETED, IngestionStatus.FAILED]:
                completed = True
            else:
                await asyncio.sleep(1.0)

    return StreamingResponse(progress_generator(), media_type="text/event-stream")

@router.post("/batch", status_code=201)
async def batch_ingest(documents: List[dict] = Body(..., embed=True)):
    if not ingestion_queue_service.is_queue_enabled():
        raise HTTPException(status_code=503, detail="Async ingestion not available. Redis not configured.")

    task_ids = []
    for doc in documents:
        task_id = await ingestion_queue_service.add_to_queue(doc)
        task_ids.append(task_id)

    return {
        "taskIds": task_ids,
        "message": f"{len(documents)} documents queued for ingestion"
    }

@router.get("/queue/enabled")
async def is_queue_enabled():
    return {"enabled": ingestion_queue_service.is_queue_enabled()}

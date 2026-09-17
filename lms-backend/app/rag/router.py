import json
import time
from fastapi import APIRouter, Request, Response, Body, UploadFile, File, Form, Query, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any

from app.auth.dependencies import get_current_user, get_current_user_optional
from app.rag.dto import (
    IngestTextDto,
    QueryDto,
    IngestVideoDto,
    CreateSessionDto,
    UpdateSessionDto
)
from app.rag.service import rag_service, IngestDocumentDto, IngestFileDto
from app.rag.streaming_service import rag_streaming_service

router = APIRouter(prefix="/v1/rag", tags=["RAG"])

@router.post("/query/stream")
async def query_stream(dto: QueryDto, current_user: Optional[dict] = Depends(get_current_user_optional)):
    user_id = current_user.get("userId") if current_user else None

    # Validate session ownership if sessionId is provided
    session_id = dto.sessionId or (dto.filters.get("sessionId") if dto.filters else None)
    if not dto.filters:
        dto.filters = {}
    if user_id:
        dto.filters["userId"] = user_id

    if session_id:
        try:
            validated_session_id = await rag_service.validate_session_ownership(session_id, user_id)
            dto.filters["sessionId"] = validated_session_id
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))

    return StreamingResponse(
        rag_streaming_service.query_stream(
            query=dto.query,
            filters=dto.filters,
            top_k=dto.topK
        ),
        media_type="text/event-stream"
    )

@router.post("/ingest/text", status_code=201)
async def ingest_text(dto: IngestTextDto):
    try:
        result = await rag_service.ingest_document(
            IngestDocumentDto(
                content=dto.content,
                fileName=dto.fileName,
                docType='text',
                metadata=dto.metadata
            )
        )
        return {
            "success": True,
            "message": "Text document ingested successfully",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest/video", status_code=201)
async def ingest_video(dto: IngestVideoDto):
    try:
        metadata = {
            **(dto.metadata or {}),
            "videoUrl": dto.videoUrl,
            "type": "video"
        }
        result = await rag_service.ingest_document(
            IngestDocumentDto(
                content=dto.transcript,
                fileName=dto.videoName,
                docType='video',
                metadata=metadata
            )
        )
        return {
            "success": True,
            "message": "Video transcript ingested successfully",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest/pdf", status_code=201)
async def ingest_pdf(file: UploadFile = File(...), metadata: Optional[str] = Form(None)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        data_buffer = await file.read()
        meta = {}
        if metadata:
            try:
                meta = json.loads(metadata)
            except Exception:
                print("Failed to parse metadata, using empty dict")

        result = await rag_service.ingest_file(
            IngestFileDto(
                fileBuffer=data_buffer,
                fileName=file.filename,
                docType="pdf",
                metadata=meta
            )
        )
        return {
            "success": True,
            "message": "PDF ingested successfully",
            "data": {
                **result,
                "fileName": file.filename
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest/document", status_code=201)
async def ingest_document(file: UploadFile = File(...), metadata: Optional[str] = Form(None)):
    allowed_mimes = ["text/plain", "text/markdown", "application/octet-stream"]
    if file.content_type not in allowed_mimes:
        ext = file.filename.split('.')[-1].lower()
        if ext not in ["txt", "md", "csv", "json"]:
            raise HTTPException(status_code=400, detail="Only text files are allowed")

    try:
        data_buffer = await file.read()
        content = data_buffer.decode("utf-8", errors="ignore")
        meta = {}
        if metadata:
            try:
                meta = json.loads(metadata)
            except Exception:
                print("Failed to parse metadata, using empty dict")

        result = await rag_service.ingest_document(
            IngestDocumentDto(
                content=content,
                fileName=file.filename,
                docType="document",
                metadata=meta
            )
        )
        return {
            "success": True,
            "message": "Document ingested successfully",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/document/{docId}")
async def delete_document(docId: str):
    try:
        await rag_service.delete_document(docId)
        return {
            "success": True,
            "message": "Document deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{docId}")
async def get_status(docId: str):
    status_data = await rag_service.get_ingestion_status(docId)
    return {
        "success": True,
        "data": status_data
    }

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "service": "lmsrag-service"
    }

# ==================== Chat Session Routes ====================

@router.post("/sessions", status_code=201)
async def create_session(dto: CreateSessionDto, current_user: dict = Depends(get_current_user)):
    user_id = current_user["userId"]
    session = await rag_service.create_chat_session(
        user_id=user_id,
        course_id=dto.courseId,
        title=dto.title,
        document_ids=dto.documentIds
    )
    return {
        "success": True,
        "message": "Chat session created successfully",
        "data": session
    }

@router.get("/sessions")
async def get_user_sessions(courseId: Optional[str] = Query(None), current_user: dict = Depends(get_current_user)):
    user_id = current_user["userId"]
    sessions = await rag_service.get_user_chat_sessions(user_id, courseId)
    return {
        "success": True,
        "data": sessions
    }

@router.get("/sessions/{sessionId}")
async def get_session(sessionId: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["userId"]
    session = await rag_service.get_chat_session(sessionId, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = await rag_service.get_session_messages(sessionId)
    return {
        "success": True,
        "data": {
            "session": session,
            "messages": messages
        }
    }

@router.patch("/sessions/{sessionId}")
async def update_session(sessionId: str, dto: UpdateSessionDto, current_user: dict = Depends(get_current_user)):
    user_id = current_user["userId"]
    try:
        await rag_service.validate_session_ownership(sessionId, user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    await rag_service.update_chat_session_title(sessionId, dto.title)
    return {
        "success": True,
        "message": "Session updated successfully"
    }

@router.delete("/sessions/{sessionId}")
async def delete_session(sessionId: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["userId"]
    try:
        await rag_service.validate_session_ownership(sessionId, user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    await rag_service.delete_chat_session(sessionId)
    return {
        "success": True,
        "message": "Session deleted successfully"
    }

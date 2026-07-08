from fastapi import APIRouter, Depends, Response, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.auth.dependencies import get_current_user, require_faculty
from app.documents.service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])
document_service = DocumentService()


@router.get("/my-documents", status_code=status.HTTP_200_OK)
async def get_my_documents(
    visibility: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty)
):
    docs = await document_service.get_documents_by_uploader(
        db=db,
        uploader_id=current_user["userId"],
        visibility=visibility
    )
    return {
        "success": True,
        "data": docs
    }


@router.get("/{id}", status_code=status.HTTP_200_OK)
async def get_document(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    doc = await document_service.get_document_by_id(
        db=db,
        id=id,
        user_id=current_user["userId"]
    )
    return {
        "success": True,
        "data": doc
    }


@router.patch("/{id}", status_code=status.HTTP_200_OK)
async def update_document(
    id: str,
    body: dict = Depends(lambda: {}),  # Will get raw request body in route handler
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty),
    request: Request = None
):
    # Retrieve JSON body manually
    json_data = await request.json()
    visibility = json_data.get("visibility")
    
    update_data = {}
    if visibility is not None:
        update_data["visibility"] = visibility

    doc = await document_service.update_document(
        db=db,
        id=id,
        uploader_id=current_user["userId"],
        update_data=update_data
    )
    
    return {
        "success": True,
        "message": "Document updated successfully",
        "data": doc
    }

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.models import Document
from app.models.enums import DocumentVisibility

class DocumentService:
    async def get_documents_by_uploader(
        self,
        db: AsyncSession,
        uploader_id: str,
        visibility: Optional[str] = None
    ) -> List[Document]:
        stmt = (
            select(Document)
            .where(Document.uploaderId == UUID(uploader_id))
            .order_by(desc(Document.createdAt))
        )
        if visibility:
            stmt = stmt.where(Document.visibility == visibility)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_document_by_id(self, db: AsyncSession, id: str, user_id: Optional[str] = None) -> Document:
        try:
            doc_uuid = UUID(id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Document not found")

        stmt = select(Document).where(Document.id == doc_uuid)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if user_id and str(document.uploaderId) == user_id:
            return document

        if document.visibility == DocumentVisibility.PRIVATE:
            raise HTTPException(status_code=403, detail="You do not have access to this document")

        return document

    async def update_document(
        self,
        db: AsyncSession,
        id: str,
        uploader_id: str,
        update_data: Dict[str, Any]
    ) -> Document:
        try:
            doc_uuid = UUID(id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Document not found")

        document = await db.get(Document, doc_uuid)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if str(document.uploaderId) != uploader_id:
            raise HTTPException(status_code=403, detail="You can only update your own documents")

        for key, value in update_data.items():
            if value is not None:
                setattr(document, key, value)

        await db.commit()
        await db.refresh(document)
        return document

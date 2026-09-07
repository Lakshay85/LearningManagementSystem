from typing import List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy import select, update, and_, desc
from app.database import AsyncSessionLocal
from app.models.rag_models import ChatSession as ChatSessionModel, ChatMessage as ChatMessageModel

class ChatSessionDto:
    def __init__(self, model: ChatSessionModel):
        self.id = str(model.id)
        self.userId = str(model.user_id)
        self.courseId = str(model.course_id) if model.course_id else None
        self.title = model.title
        self.documentIds = model.document_ids or []
        self.summary = model.summary
        self.messageCount = model.message_count or 0
        self.isActive = model.is_active
        self.createdAt = model.created_at
        self.updatedAt = model.updated_at
        self.lastActivityAt = model.last_activity_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "userId": self.userId,
            "courseId": self.courseId,
            "title": self.title,
            "documentIds": self.documentIds,
            "summary": self.summary,
            "messageCount": self.messageCount,
            "isActive": self.isActive,
            "createdAt": self.createdAt.isoformat() if isinstance(self.createdAt, datetime) else str(self.createdAt) if self.createdAt else None,
            "updatedAt": self.updatedAt.isoformat() if isinstance(self.updatedAt, datetime) else str(self.updatedAt) if self.updatedAt else None,
            "lastActivityAt": self.lastActivityAt.isoformat() if isinstance(self.lastActivityAt, datetime) else str(self.lastActivityAt) if self.lastActivityAt else None
        }

class ChatMessageDto:
    def __init__(self, model: ChatMessageModel):
        self.id = str(model.id)
        self.sessionId = str(model.session_id)
        self.role = model.role
        self.content = model.content
        self.sources = model.sources or []
        self.tokenCount = model.token_count or 0
        self.createdAt = model.created_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sessionId": self.sessionId,
            "role": self.role,
            "content": self.content,
            "sources": self.sources,
            "tokenCount": self.tokenCount,
            "createdAt": self.createdAt.isoformat() if isinstance(self.createdAt, datetime) else str(self.createdAt) if self.createdAt else None
        }

class ChatMemoryService:
    def __init__(self):
        self.context_window_size = 10

    async def create_session(
        self,
        user_id: str,
        course_id: Optional[str] = None,
        title: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> ChatSessionDto:
        async with AsyncSessionLocal() as session:
            new_session = ChatSessionModel(
                user_id=UUID(user_id),
                course_id=UUID(course_id) if course_id else None,
                title=title or "New Chat",
                document_ids=document_ids or [],
                message_count=0,
                is_active=True
            )
            session.add(new_session)
            await session.commit()
            await session.refresh(new_session)
            print(f"📝 Created chat session: {new_session.id}")
            return ChatSessionDto(new_session)

    async def get_session(self, session_id: str) -> Optional[ChatSessionDto]:
        try:
            session_uuid = UUID(session_id)
        except ValueError:
            return None

        async with AsyncSessionLocal() as session:
            stmt = select(ChatSessionModel).where(ChatSessionModel.id == session_uuid)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            return ChatSessionDto(model) if model else None

    async def get_user_sessions(self, user_id: str, limit: int = 20) -> List[ChatSessionDto]:
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            return []

        async with AsyncSessionLocal() as session:
            stmt = (
                select(ChatSessionModel)
                .where(and_(
                    ChatSessionModel.user_id == user_uuid,
                    ChatSessionModel.is_active == True,
                    ChatSessionModel.message_count > 0
                ))
                .order_by(desc(ChatSessionModel.last_activity_at))
                .limit(limit)
            )
            res = await session.execute(stmt)
            models = res.scalars().all()
            return [ChatSessionDto(m) for m in models]

    async def get_course_sessions_for_user(self, user_id: str, course_id: str) -> List[ChatSessionDto]:
        try:
            user_uuid = UUID(user_id)
            course_uuid = UUID(course_id)
        except ValueError:
            return []

        async with AsyncSessionLocal() as session:
            stmt = (
                select(ChatSessionModel)
                .where(and_(
                    ChatSessionModel.user_id == user_uuid,
                    ChatSessionModel.course_id == course_uuid,
                    ChatSessionModel.is_active == True,
                    ChatSessionModel.message_count > 0
                ))
                .order_by(desc(ChatSessionModel.last_activity_at))
            )
            res = await session.execute(stmt)
            models = res.scalars().all()
            return [ChatSessionDto(m) for m in models]

    async def update_session_title(self, session_id: str, title: str):
        try:
            session_uuid = UUID(session_id)
        except ValueError:
            return

        async with AsyncSessionLocal() as session:
            stmt = (
                update(ChatSessionModel)
                .where(ChatSessionModel.id == session_uuid)
                .values(title=title, updated_at=datetime.now())
            )
            await session.execute(stmt)
            await session.commit()

    async def delete_session(self, session_id: str):
        try:
            session_uuid = UUID(session_id)
        except ValueError:
            return

        async with AsyncSessionLocal() as session:
            stmt = (
                update(ChatSessionModel)
                .where(ChatSessionModel.id == session_uuid)
                .values(is_active=False, updated_at=datetime.now())
            )
            await session.execute(stmt)
            await session.commit()
            print(f"🗑️ Deleted chat session: {session_id}")

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[dict]] = None,
        token_count: int = 0
    ) -> ChatMessageDto:
        session_uuid = UUID(session_id)
        now = datetime.now()

        async with AsyncSessionLocal() as session:
            new_msg = ChatMessageModel(
                session_id=session_uuid,
                role=role,
                content=content,
                sources=sources or [],
                token_count=token_count
            )
            session.add(new_msg)

            # Update session activity and message count
            stmt = (
                update(ChatSessionModel)
                .where(ChatSessionModel.id == session_uuid)
                .values(
                    message_count=ChatSessionModel.message_count + 1,
                    last_activity_at=now,
                    updated_at=now
                )
            )
            await session.execute(stmt)
            await session.commit()
            await session.refresh(new_msg)
            return ChatMessageDto(new_msg)

    async def get_session_messages(self, session_id: str, limit: int = 50) -> List[ChatMessageDto]:
        try:
            session_uuid = UUID(session_id)
        except ValueError:
            return []

        async with AsyncSessionLocal() as session:
            stmt = (
                select(ChatMessageModel)
                .where(ChatMessageModel.session_id == session_uuid)
                .order_by(ChatMessageModel.created_at.asc())
                .limit(limit)
            )
            res = await session.execute(stmt)
            models = res.scalars().all()
            return [ChatMessageDto(m) for m in models]

    async def get_recent_messages(self, session_id: str, limit: Optional[int] = None) -> List[ChatMessageDto]:
        try:
            session_uuid = UUID(session_id)
        except ValueError:
            return []

        msg_limit = limit or self.context_window_size
        async with AsyncSessionLocal() as session:
            stmt = (
                select(ChatMessageModel)
                .where(ChatMessageModel.session_id == session_uuid)
                .order_by(ChatMessageModel.created_at.desc())
                .limit(msg_limit)
            )
            res = await session.execute(stmt)
            models = res.scalars().all()
            # Return in chronological order
            return [ChatMessageDto(m) for m in reversed(models)]

    async def build_conversation_context(self, session_id: str) -> str:
        session = await self.get_session(session_id)
        messages = await self.get_recent_messages(session_id)

        if not messages and (not session or not session.summary):
            return ""

        context = ""
        if session and session.summary:
            context += f"CONVERSATION SUMMARY (earlier messages):\n{session.summary}\n\n---\n"

        if messages:
            formatted = []
            for m in messages:
                if m.role == "system":
                    continue
                role_label = "Student" if m.role == "user" else "Assistant"
                formatted.append(f"{role_label}: {m.content}")
            
            context += f"\nRECENT MESSAGES:\n{chr(10).join(formatted)}\n\n---\n"

        return context

    async def get_session_summary(self, session_id: str) -> Optional[str]:
        session = await self.get_session(session_id)
        return session.summary if session else None

    async def update_session_summary(self, session_id: str, summary: str):
        try:
            session_uuid = UUID(session_id)
        except ValueError:
            return

        async with AsyncSessionLocal() as session:
            stmt = (
                update(ChatSessionModel)
                .where(ChatSessionModel.id == session_uuid)
                .values(summary=summary, updated_at=datetime.now())
            )
            await session.execute(stmt)
            await session.commit()

# Global chat memory service instance
chat_memory_service = ChatMemoryService()

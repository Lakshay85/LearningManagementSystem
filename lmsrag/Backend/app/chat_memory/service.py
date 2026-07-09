import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.config import settings
from app.database.service import db_service

class ChatSession:
    def __init__(self, row: dict):
        self.id = str(row["id"])
        self.userId = str(row["user_id"])
        self.courseId = str(row["course_id"]) if row.get("course_id") else None
        self.title = row["title"]
        self.documentIds = row.get("document_ids") or []
        self.summary = row.get("summary")
        self.messageCount = row["message_count"]
        self.isActive = row["is_active"]
        self.createdAt = row["created_at"]
        self.updatedAt = row["updated_at"]
        self.lastActivityAt = row["last_activity_at"]

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
            "createdAt": self.createdAt.isoformat() if isinstance(self.createdAt, datetime) else self.createdAt,
            "updatedAt": self.updatedAt.isoformat() if isinstance(self.updatedAt, datetime) else self.updatedAt,
            "lastActivityAt": self.lastActivityAt.isoformat() if isinstance(self.lastActivityAt, datetime) else self.lastActivityAt
        }

class ChatMessage:
    def __init__(self, row: dict):
        self.id = str(row["id"])
        self.sessionId = str(row["session_id"])
        self.role = row["role"]
        self.content = row["content"]
        sources_raw = row.get("sources") or []
        self.sources = json.loads(sources_raw) if isinstance(sources_raw, str) else sources_raw
        self.tokenCount = row.get("token_count") or 0
        self.createdAt = row["created_at"]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sessionId": self.sessionId,
            "role": self.role,
            "content": self.content,
            "sources": self.sources,
            "tokenCount": self.tokenCount,
            "createdAt": self.createdAt.isoformat() if isinstance(self.createdAt, datetime) else self.createdAt
        }

class ChatMemoryService:
    def __init__(self):
        self.context_window_size = 10

    async def create_session(self, dto: dict) -> ChatSession:
        query = """
            INSERT INTO chat_sessions (user_id, course_id, title, document_ids)
            VALUES ($1, $2, $3, $4)
            RETURNING *
        """
        # Ensure UUID formats are strings
        user_id = str(dto["userId"])
        course_id = str(dto["courseId"]) if dto.get("courseId") else None
        title = dto.get("title") or "New Chat"
        document_ids = dto.get("documentIds") or []

        rows = await db_service.query(query, user_id, course_id, title, document_ids)
        session = ChatSession(dict(rows[0]))
        
        print(f"📝 Created chat session: {session.id}")
        return session

    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        rows = await db_service.query("SELECT * FROM chat_sessions WHERE id = $1", session_id)
        if not rows:
            return None

        session = ChatSession(dict(rows[0]))
        return session

    async def get_user_sessions(self, user_id: str, limit: int = 20) -> List[ChatSession]:
        query = """
            SELECT * FROM chat_sessions 
            WHERE user_id = $1 AND is_active = true AND message_count > 0
            ORDER BY last_activity_at DESC 
            LIMIT $2
        """
        rows = await db_service.query(query, user_id, limit)
        return [ChatSession(dict(row)) for row in rows]

    async def get_course_sessions_for_user(self, user_id: str, course_id: str) -> List[ChatSession]:
        query = """
            SELECT * FROM chat_sessions 
            WHERE user_id = $1 AND course_id = $2 AND is_active = true AND message_count > 0
            ORDER BY last_activity_at DESC
        """
        rows = await db_service.query(query, user_id, course_id)
        return [ChatSession(dict(row)) for row in rows]

    async def update_session_title(self, session_id: str, title: str):
        await db_service.execute(
            "UPDATE chat_sessions SET title = $2, updated_at = CURRENT_TIMESTAMP WHERE id = $1",
            session_id, title
        )

    async def delete_session(self, session_id: str):
        await db_service.execute(
            "UPDATE chat_sessions SET is_active = false, updated_at = CURRENT_TIMESTAMP WHERE id = $1",
            session_id
        )
        print(f"🗑️ Deleted chat session: {session_id}")

    async def add_message(self, dto: dict) -> ChatMessage:
        if not db_service.pool:
            await db_service.connect()
            
        async with db_service.pool.acquire() as connection:
            async with connection.transaction():
                # Insert message
                message_row = await connection.fetchrow(
                    """
                    INSERT INTO chat_messages (session_id, role, content, sources, token_count)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING *
                    """,
                    dto["sessionId"],
                    dto["role"],
                    dto["content"],
                    json.dumps(dto.get("sources") or []),
                    dto.get("tokenCount") or 0
                )
                
                # Update session
                await connection.execute(
                    """
                    UPDATE chat_sessions 
                    SET message_count = message_count + 1, 
                        last_activity_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                    """,
                    dto["sessionId"]
                )
                
        message = ChatMessage(dict(message_row))
        return message

    async def get_session_messages(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        query = """
            SELECT * FROM chat_messages 
            WHERE session_id = $1 
            ORDER BY created_at ASC 
            LIMIT $2
        """
        rows = await db_service.query(query, session_id, limit)
        return [ChatMessage(dict(row)) for row in rows]

    async def get_recent_messages(self, session_id: str, limit: Optional[int] = None) -> List[ChatMessage]:
        message_limit = limit or self.context_window_size

        query = """
            SELECT * FROM chat_messages 
            WHERE session_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2
        """
        rows = await db_service.query(query, session_id, message_limit)
        
        # Return in chronological order
        reversed_rows = list(reversed(rows))
        return [ChatMessage(dict(row)) for row in reversed_rows]

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
                role = "Student" if m.role == "user" else "Assistant"
                formatted.append(f"{role}: {m.content}")
            
            context += f"\nRECENT MESSAGES:\n{chr(10).join(formatted)}\n\n---\n"

        return context

    async def get_session_summary(self, session_id: str) -> Optional[str]:
        session = await self.get_session(session_id)
        return session.summary if session else None

    async def update_session_summary(self, session_id: str, summary: str):
        await db_service.execute(
            "UPDATE chat_sessions SET summary = $2, updated_at = CURRENT_TIMESTAMP WHERE id = $1",
            session_id, summary
        )

# Global chat memory service instance
chat_memory_service = ChatMemoryService()

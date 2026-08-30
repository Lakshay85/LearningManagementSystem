import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, 
    Numeric, Text, Index, UniqueConstraint, BigInteger, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship as orm_relationship
from app.database import Base

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy.types import UserDefinedType
    class Vector(UserDefinedType):
        def __init__(self, dim=1024):
            self.dim = dim
        def get_col_spec(self, **kw):
            return f"vector({self.dim})"

class RagDocument(Base):
    __tablename__ = 'rag_documents'
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    doc_id = Column(Text, nullable=False, index=True)
    doc_name = Column(Text, nullable=False)
    doc_type = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1024), nullable=True)
    metadata_json = Column("metadata", JSONB, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class RagIngestionJob(Base):
    __tablename__ = 'rag_ingestion_jobs'
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    doc_id = Column(Text, nullable=False, unique=True, index=True)
    doc_name = Column(Text, nullable=False)
    doc_type = Column(Text, nullable=False)
    status = Column(Text, nullable=False, index=True)  # 'processing', 'completed', 'failed'
    total_chunks = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id', ondelete='SET NULL'), nullable=True, index=True)
    title = Column(Text, default='New Chat')
    document_ids = Column(ARRAY(Text), default=list)
    summary = Column(Text, nullable=True)
    message_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_activity_at = Column(DateTime, server_default=func.now(), index=True)

    user = orm_relationship("User")
    course = orm_relationship("Course")
    messages = orm_relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    sources = Column(JSONB, default=list)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    session = orm_relationship("ChatSession", back_populates="messages")

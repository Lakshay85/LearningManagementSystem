import sys
import asyncio
from sqlalchemy import text
from app.database import engine, Base
import app.models  # Ensure all models are registered on Base.metadata

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

INIT_RAG_SQL = """
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Ensure vector index on rag_documents
CREATE INDEX IF NOT EXISTS rag_documents_embedding_cosine_idx
  ON rag_documents USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Ensure doc_id index
CREATE INDEX IF NOT EXISTS rag_documents_doc_id_idx ON rag_documents(doc_id);

-- Ensure metadata GIN index
CREATE INDEX IF NOT EXISTS rag_documents_metadata_idx ON rag_documents USING gin(metadata);

-- Structure-aware indexes for filtering
CREATE INDEX IF NOT EXISTS rag_documents_element_type_idx ON rag_documents ((metadata->>'elementType'));
CREATE INDEX IF NOT EXISTS rag_documents_section_idx ON rag_documents ((metadata->>'section'));
CREATE INDEX IF NOT EXISTS rag_documents_content_category_idx ON rag_documents ((metadata->>'contentCategory'));

-- Chat session indexes
CREATE INDEX IF NOT EXISTS chat_sessions_user_id_idx ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS chat_sessions_course_id_idx ON chat_sessions(course_id);
CREATE INDEX IF NOT EXISTS chat_sessions_active_idx ON chat_sessions(is_active, last_activity_at DESC);

-- Chat messages indexes
CREATE INDEX IF NOT EXISTS chat_messages_session_id_idx ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS chat_messages_created_at_idx ON chat_messages(session_id, created_at);

-- Quiz indexes and constraints
CREATE INDEX IF NOT EXISTS quizzes_course_id_idx ON quizzes("courseId");
CREATE INDEX IF NOT EXISTS quizzes_status_idx ON quizzes(status);
CREATE INDEX IF NOT EXISTS quiz_questions_quiz_id_idx ON quiz_questions("quizId");
CREATE INDEX IF NOT EXISTS quiz_submissions_quiz_student_idx ON quiz_submissions("quizId", "studentId");

-- Course contents quiz column migration
ALTER TABLE course_contents ADD COLUMN IF NOT EXISTS "quizId" UUID REFERENCES quizzes(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS course_contents_quiz_id_idx ON course_contents("quizId");
"""

async def init_database():
    """
    Initializes database tables, vector extension, and indexes on startup.
    """
    print("[Database] Initializing database schema and pgvector extension...")
    async with engine.begin() as conn:
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        except Exception as e:
            print(f"[Database] Vector extension notice: {str(e)}")

        # Create all tables defined in SQLAlchemy Base
        await conn.run_sync(Base.metadata.create_all)

        # Execute custom indexes and pgvector index statements
        for statement in INIT_RAG_SQL.strip().split(";"):
            stmt = statement.strip()
            if stmt:
                try:
                    await conn.execute(text(stmt))
                except Exception as e:
                    pass
    print("[Database] Database schema and vector tables initialized successfully")

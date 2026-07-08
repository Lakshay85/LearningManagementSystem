-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create documents table for storing document chunks with embeddings
CREATE TABLE IF NOT EXISTS documents (
  id BIGSERIAL PRIMARY KEY,
  doc_id TEXT NOT NULL,
  doc_name TEXT NOT NULL,
  doc_type TEXT NOT NULL, -- 'pdf', 'text', 'video', etc.
  chunk_index INTEGER NOT NULL,
  content TEXT NOT NULL,
  embedding VECTOR(1024), -- NVIDIA bge-m3 dimension
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for vector similarity search (cosine distance)
CREATE INDEX IF NOT EXISTS documents_embedding_cosine_idx
  ON documents USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Create index for doc_id lookups
CREATE INDEX IF NOT EXISTS documents_doc_id_idx ON documents(doc_id);

-- Create index for metadata queries
CREATE INDEX IF NOT EXISTS documents_metadata_idx ON documents USING gin(metadata);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE
    ON documents FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create table for tracking document ingestion status
CREATE TABLE IF NOT EXISTS ingestion_jobs (
  id BIGSERIAL PRIMARY KEY,
  doc_id TEXT NOT NULL UNIQUE,
  doc_name TEXT NOT NULL,
  doc_type TEXT NOT NULL,
  status TEXT NOT NULL, -- 'processing', 'completed', 'failed'
  total_chunks INTEGER DEFAULT 0,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ingestion_jobs_status_idx ON ingestion_jobs(status);
CREATE INDEX IF NOT EXISTS ingestion_jobs_doc_id_idx ON ingestion_jobs(doc_id);

-- Chat Sessions table for storing conversation sessions
CREATE TABLE IF NOT EXISTS chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  course_id UUID,  -- Optional: link to specific course
  title TEXT DEFAULT 'New Chat',
  document_ids TEXT[] DEFAULT '{}',  -- Array of associated document IDs
  summary TEXT,  -- Compressed summary for long conversations
  message_count INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS chat_sessions_user_id_idx ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS chat_sessions_course_id_idx ON chat_sessions(course_id);
CREATE INDEX IF NOT EXISTS chat_sessions_active_idx ON chat_sessions(is_active, last_activity_at DESC);

-- Chat Messages table for storing individual messages
CREATE TABLE IF NOT EXISTS chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  sources JSONB DEFAULT '[]'::jsonb,  -- Array of source citations
  token_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS chat_messages_session_id_idx ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS chat_messages_created_at_idx ON chat_messages(session_id, created_at);

-- Update trigger for chat_sessions
CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE
    ON chat_sessions FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

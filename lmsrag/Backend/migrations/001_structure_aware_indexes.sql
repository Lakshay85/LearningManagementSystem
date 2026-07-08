-- Migration: Add indexes for structure-aware RAG metadata
-- Run this after the initial schema creation

-- Index for element type queries (for type-based filtering)
CREATE INDEX IF NOT EXISTS documents_element_type_idx
  ON documents ((metadata->>'elementType'));

-- Index for section-based queries
CREATE INDEX IF NOT EXISTS documents_section_idx
  ON documents ((metadata->>'section'));

-- Index for content category queries
CREATE INDEX IF NOT EXISTS documents_content_category_idx
  ON documents ((metadata->>'contentCategory'));

-- Composite index for common query patterns
CREATE INDEX IF NOT EXISTS documents_doc_type_element_idx
  ON documents (doc_type, (metadata->>'elementType'));

-- Index for numeric content filtering
CREATE INDEX IF NOT EXISTS documents_has_numeric_idx
  ON documents ((metadata->>'containsNumbers'))
  WHERE metadata->>'containsNumbers' = 'true';

-- Index for search boost optimization
CREATE INDEX IF NOT EXISTS documents_search_boost_idx
  ON documents (((metadata->>'searchBoost')::float))
  WHERE metadata->>'searchBoost' IS NOT NULL;

-- Add comment for migration tracking
COMMENT ON INDEX documents_element_type_idx IS 'Structure-aware RAG: element type filtering';
COMMENT ON INDEX documents_section_idx IS 'Structure-aware RAG: section-based queries';
COMMENT ON INDEX documents_content_category_idx IS 'Structure-aware RAG: content category filtering';

import json
import re
from typing import List, Dict, Any, Optional

from app.rag.db_service import rag_db_service
from app.rag.ingestion.embedder import Embedder
from app.rag.structure.query_analyzer import QueryAnalyzer, QueryAnalysis, QueryType
from app.rag.structure.types import ElementType

class RetrievalConfig:
    def __init__(
        self,
        topK: int = 20,
        similarityThreshold: float = 0.25,
        fallbackThreshold: float = 0.15,
        minimumThreshold: float = 0.10,
        useQueryAnalysis: bool = True,
        diversityFactor: float = 0.05,
        useKeywordFallback: bool = True,
        expandContext: bool = True,
        contextWindowSize: int = 2
    ):
        self.topK = topK
        self.similarityThreshold = similarityThreshold
        self.fallbackThreshold = fallbackThreshold
        self.minimumThreshold = minimumThreshold
        self.useQueryAnalysis = useQueryAnalysis
        self.diversityFactor = diversityFactor
        self.useKeywordFallback = useKeywordFallback
        self.expandContext = expandContext
        self.contextWindowSize = contextWindowSize

    def to_dict(self) -> dict:
        return self.__dict__

class RetrievedChunk:
    def __init__(
        self,
        id: int,
        docId: str,
        docName: str,
        docType: str,
        chunkIndex: int,
        content: str,
        similarity: float,
        boostedScore: float,
        metadata: Dict[str, Any],
        matchType: str = "vector"
    ):
        self.id = id
        self.docId = docId
        self.docName = docName
        self.docType = docType
        self.chunkIndex = chunkIndex
        self.content = content
        self.similarity = similarity
        self.boostedScore = boostedScore
        self.metadata = metadata
        self.matchType = matchType

    def to_dict(self) -> dict:
        return self.__dict__

class RetrievalResult:
    def __init__(
        self,
        chunks: List[RetrievedChunk],
        queryAnalysis: Optional[QueryAnalysis],
        stats: Dict[str, Any]
    ):
        self.chunks = chunks
        self.queryAnalysis = queryAnalysis
        self.stats = stats

    def to_dict(self) -> dict:
        return {
            "chunks": [c.to_dict() for c in self.chunks],
            "queryAnalysis": self.queryAnalysis.to_dict() if self.queryAnalysis else None,
            "stats": self.stats
        }

class SmartRetriever:
    def __init__(
        self,
        db=None,
        embedder: Optional[Embedder] = None,
        config: Optional[dict] = None
    ):
        self.db = db or rag_db_service
        self.embedder = embedder or Embedder.create_from_env()
        cfg = config or {}
        self.config = RetrievalConfig(
            topK=cfg.get("topK", 20),
            similarityThreshold=cfg.get("similarityThreshold", 0.25),
            fallbackThreshold=cfg.get("fallbackThreshold", 0.15),
            minimumThreshold=cfg.get("minimumThreshold", 0.10),
            useQueryAnalysis=cfg.get("useQueryAnalysis", True),
            diversityFactor=cfg.get("diversityFactor", 0.05),
            useKeywordFallback=cfg.get("useKeywordFallback", True),
            expandContext=cfg.get("expandContext", True),
            contextWindowSize=cfg.get("contextWindowSize", 2)
        )
        self.query_analyzer = QueryAnalyzer()

    async def retrieve(
        self,
        query: str,
        filters: Optional[dict] = None,
        top_k: Optional[int] = None
    ) -> RetrievalResult:
        import time
        start_time = time.time()
        effective_top_k = top_k or self.config.topK

        analysis = None
        if self.config.useQueryAnalysis:
            analysis = self.query_analyzer.analyze(query)
            print(f"📊 Query Analysis: Type={analysis.queryType.value}, Preferred={[t.value for t in analysis.preferredElementTypes]}")

        query_embedding = await self.embedder.embed_query(query)

        search_k = min(effective_top_k * 2, 50)
        raw_results = await self.db.similarity_search(query_embedding, search_k, filters)

        for r in raw_results:
            r["boostedScore"] = r["similarity"]
            r["matchType"] = "vector"

        if analysis:
            raw_results = self.query_analyzer.apply_boosts(raw_results, analysis)

        filtered = [r for r in raw_results if r["similarity"] >= self.config.similarityThreshold]

        if not filtered and self.config.useKeywordFallback:
            print(f"⚠️ Vector search returned 0 results above threshold ({self.config.similarityThreshold}), trying fallback...")
            filtered = [r for r in raw_results if r["similarity"] >= self.config.fallbackThreshold]
            
            if not filtered:
                key_terms = self.extract_search_terms(query)
                if key_terms:
                    print(f"🔍 Keyword search fallback for terms: {', '.join(key_terms)}")
                    keyword_results = await self.keyword_search(key_terms, effective_top_k, filters)
                    filtered = keyword_results

        filtered.sort(key=lambda x: x.get("boostedScore", x["similarity"]), reverse=True)
        diversified = self.diversify_results(filtered, effective_top_k)

        chunks = [
            RetrievedChunk(
                id=r["id"],
                docId=r["doc_id"],
                docName=r["doc_name"],
                docType=r["doc_type"],
                chunkIndex=r["chunk_index"],
                content=r["content"],
                similarity=r["similarity"],
                boostedScore=r.get("boostedScore", r["similarity"]),
                metadata=r["metadata"] or {},
                matchType=r.get("matchType", "vector")
            )
            for r in diversified
        ]

        if self.config.expandContext and chunks:
            chunks = await self.expand_context(chunks, self.config.contextWindowSize)

        processing_time = int((time.time() - start_time) * 1000)

        return RetrievalResult(
            chunks=chunks,
            queryAnalysis=analysis,
            stats={
                "totalRetrieved": len(raw_results),
                "afterThreshold": len(filtered),
                "afterDiversity": len(diversified),
                "finalCount": len(chunks),
                "processingTimeMs": processing_time
            }
        )

    def extract_search_terms(self, query: str) -> List[str]:
        terms = []
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'what', 'where',
            'who', 'how', 'when', 'why', 'which', 'can', 'could', 'would', 'should',
            'does', 'did', 'do', 'have', 'has', 'had', 'tell', 'me', 'about', 'find'
        }

        quotes = re.findall(r'"([^"]+)"', query)
        terms.extend(quotes)

        clean = re.sub(r"[^\w\s]", " ", query)
        words = clean.split()
        for noun in words:
            if noun.lower() not in stop_words and len(noun) > 2:
                terms.append(noun.lower())

        numbers = re.findall(r"\b\d+\b", query)
        terms.extend(numbers)

        return list(dict.fromkeys(terms))

    async def keyword_search(
        self,
        key_terms: List[str],
        top_k: int,
        filter_dict: Optional[dict] = None
    ) -> List[dict]:
        if not key_terms:
            return []

        try:
            from sqlalchemy import text
            from app.database import AsyncSessionLocal

            or_conditions = []
            params = {}
            for i, term in enumerate(key_terms):
                param_key = f"term_{i}"
                or_conditions.append(f"LOWER(content) LIKE LOWER(:{param_key})")
                params[param_key] = f"%{term}%"

            query_sql = f"""
                SELECT 
                  id, doc_id, doc_name, doc_type, chunk_index, content, metadata,
                  0.5 AS similarity
                FROM rag_documents
                WHERE ({' OR '.join(or_conditions)})
            """

            if filter_dict:
                query_sql += f" AND metadata @> CAST(:filter_meta AS jsonb)"
                params["filter_meta"] = json.dumps(filter_dict)

            query_sql += " LIMIT :limit"
            params["limit"] = top_k

            async with AsyncSessionLocal() as session:
                result = await session.execute(text(query_sql), params)
                rows = result.fetchall()
                columns = result.keys()

            results = []
            for r in rows:
                row = dict(zip(columns, r))
                content = row["content"].lower()
                match_count = sum(1 for term in key_terms if term.lower() in content)
                score = 0.3 + (match_count / len(key_terms)) * 0.5

                meta = row["metadata"]
                if isinstance(meta, str):
                    meta = json.loads(meta)

                results.append({
                    "id": row["id"],
                    "doc_id": row["doc_id"],
                    "doc_name": row["doc_name"],
                    "doc_type": row["doc_type"],
                    "chunk_index": row["chunk_index"],
                    "content": row["content"],
                    "metadata": meta,
                    "similarity": score,
                    "boostedScore": score,
                    "matchType": "keyword"
                })

            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results
        except Exception as e:
            print(f"Keyword search failed: {str(e)}")
            return []

    def diversify_results(self, results: List[dict], max_results: int) -> List[dict]:
        if len(results) <= max_results:
            return results

        selected = []
        doc_counts = {}
        section_counts = {}

        for r in results:
            if len(selected) >= max_results:
                break

            doc_id = r["doc_id"]
            meta = r.get("metadata") or {}
            section = meta.get("section", "default")

            doc_count = doc_counts.get(doc_id, 0)
            section_count = section_counts.get(section, 0)

            penalty = (doc_count * self.config.diversityFactor) + (section_count * self.config.diversityFactor * 0.5)
            adjusted_score = r.get("boostedScore", r["similarity"]) * (1 - penalty)

            if adjusted_score >= self.config.minimumThreshold:
                selected.append(r)
                doc_counts[doc_id] = doc_count + 1
                section_counts[section] = section_count + 1

        if len(selected) < max_results:
            for r in results:
                if r not in selected and len(selected) < max_results:
                    selected.append(r)

        return selected

    async def expand_context(self, chunks: List[RetrievedChunk], window_size: int = 2) -> List[RetrievedChunk]:
        if not chunks or window_size <= 0:
            return chunks

        from sqlalchemy import text
        from app.database import AsyncSessionLocal

        by_doc = {}
        for c in chunks:
            by_doc.setdefault(c.docId, []).append(c)

        expanded = []
        added_ids = set()

        for doc_id, doc_chunks in by_doc.items():
            needed = set()
            for c in doc_chunks:
                needed.add(c.chunkIndex)
                for i in range(1, window_size + 1):
                    if c.chunkIndex - i >= 0:
                        needed.add(c.chunkIndex - i)
                    needed.add(c.chunkIndex + i)

            try:
                indices = sorted(list(needed))
                query_sql = """
                    SELECT id, doc_id, doc_name, doc_type, chunk_index, content, metadata,
                           0.5 AS similarity
                    FROM rag_documents
                    WHERE doc_id = :doc_id AND chunk_index = ANY(:indices)
                    ORDER BY chunk_index ASC
                """
                
                async with AsyncSessionLocal() as session:
                    result = await session.execute(text(query_sql), {"doc_id": doc_id, "indices": indices})
                    rows = result.fetchall()
                    columns = result.keys()

                for r in rows:
                    row = dict(zip(columns, r))
                    row_id = row["id"]
                    if row_id not in added_ids:
                        added_ids.add(row_id)
                        
                        original = next((c for c in doc_chunks if c.chunkIndex == row["chunk_index"]), None)
                        
                        meta = row["metadata"]
                        if isinstance(meta, str):
                            meta = json.loads(meta)

                        expanded.append(RetrievedChunk(
                            id=row_id,
                            docId=row["doc_id"],
                            docName=row["doc_name"],
                            docType=row["doc_type"],
                            chunkIndex=row["chunk_index"],
                            content=row["content"],
                            similarity=original.similarity if original else 0.5,
                            boostedScore=original.boostedScore if original else 0.5,
                            metadata=meta,
                            matchType=original.matchType if original else 'context'
                        ))
            except Exception as e:
                print(f"Failed to expand context for doc {doc_id}: {str(e)}")
                for c in doc_chunks:
                    if c.id not in added_ids:
                        added_ids.add(c.id)
                        expanded.append(c)

        expanded.sort(key=lambda x: (x.docId, x.chunkIndex))
        print(f"Context expansion: {len(chunks)} -> {len(expanded)} chunks")
        return expanded

    async def retrieve_with_fallback(
        self,
        query: str,
        filters: Optional[dict] = None,
        top_k: Optional[int] = None
    ) -> RetrievalResult:
        return await self.retrieve(query, filters, top_k)

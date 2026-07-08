import json
from typing import List, Dict, Any, Optional

from app.database.service import db_service, DatabaseService
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
        metadata: dict,
        matchType: str = 'semantic'
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
        return {
            "id": self.id,
            "docId": self.docId,
            "docName": self.docName,
            "docType": self.docType,
            "chunkIndex": self.chunkIndex,
            "content": self.content,
            "similarity": self.similarity,
            "boostedScore": self.boostedScore,
            "metadata": self.metadata,
            "matchType": self.matchType
        }

class RetrievalResult:
    def __init__(
        self,
        chunks: List[RetrievedChunk],
        query_analysis: QueryAnalysis,
        total_candidates: int,
        filtered: int,
        retrieval_method: str
    ):
        self.chunks = chunks
        self.queryAnalysis = query_analysis
        self.totalCandidates = total_candidates
        self.filtered = filtered
        self.retrievalMethod = retrieval_method

    def to_dict(self) -> dict:
        return {
            "chunks": [c.to_dict() for c in self.chunks],
            "queryAnalysis": self.queryAnalysis.to_dict() if hasattr(self.queryAnalysis, "to_dict") else self.queryAnalysis,
            "totalCandidates": self.totalCandidates,
            "filtered": self.filtered,
            "retrievalMethod": self.retrievalMethod
        }

class SmartRetriever:
    def __init__(
        self,
        db: DatabaseService,
        embedder: Embedder,
        config: dict = None
    ):
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
        self.db = db
        self.embedder = embedder
        self.query_analyzer = QueryAnalyzer()

    def extract_key_terms(self, query: str) -> List[str]:
        lower = query.lower()
        terms = []

        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
            'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
            'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'between', 'under', 'again', 'further', 'then', 'once',
            'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
            'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
            'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'just', 'don',
            'now', 'this', 'that', 'these', 'those', 'what', 'which', 'who',
            'whom', 'his', 'her', 'its', 'their', 'my', 'your', 'our',
            'document', 'pdf', 'file', 'mentioned', 'about', 'tell', 'me'
        }

        # Extract words
        words = re.findall(r"\b[a-z]+\b", lower)
        for w in words:
            if w not in stop_words and len(w) > 2:
                terms.append(w)

        # Capitalized proper nouns
        proper_nouns = re.findall(r"\b[A-Z][a-z]+\b", query)
        for noun in proper_nouns:
            if noun.lower() not in stop_words:
                terms.append(noun.lower())

        # Numbers
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
            or_conditions = []
            for i in range(len(key_terms)):
                or_conditions.append(f"LOWER(content) LIKE LOWER(${i + 2})")

            query = f"""
                SELECT 
                  id, doc_id, doc_name, doc_type, chunk_index, content, metadata,
                  0.5 AS similarity
                FROM documents
                WHERE ({' OR '.join(or_conditions)})
            """
            
            params = [top_k]
            for term in key_terms:
                params.append(f"%{term}%")

            if filter_dict:
                query += f" AND metadata @> ${len(params) + 1}::jsonb"
                params.append(json.dumps(filter_dict))

            query += " LIMIT $1"

            rows = await self.db.query(query, *params)
            
            results = []
            for row in rows:
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

    async def retrieve(
        self,
        query: str,
        filters: Optional[dict] = None,
        top_k: Optional[int] = None
    ) -> RetrievalResult:
        effective_top_k = top_k or self.config.topK

        # Step 1: Analyze query
        analysis = self.query_analyzer.analyze(query) if self.config.useQueryAnalysis else self.get_default_analysis(query)
        print(f"📊 Query Analysis: type={analysis.queryType}, preferred={', '.join([t.value if isinstance(t, ElementType) else t for t in analysis.preferredElementTypes])}")

        # Step 2: Generate embedding
        query_embedding = await self.embedder.embed_query(query)

        # Step 3: Fetch candidate count
        candidate_count = effective_top_k * 3
        print(f"🔍 Searching with topK={candidate_count}, filters={filters}")
        results = await self.db.similarity_search(query_embedding, candidate_count, filters)

        # Format DB results into dicts
        boosted_results = self.apply_smart_boosting(results, analysis)

        # Apply diversity re-ranking
        diverse = self.apply_diversity_reranking(boosted_results, effective_top_k)

        # Filter by threshold
        filtered = [r for r in diverse if r["boostedScore"] >= self.config.similarityThreshold]

        # Map to RetrievedChunk
        chunks = []
        for r in filtered:
            chunks.append(self.format_chunk(r, 'semantic'))

        # Expand context
        if self.config.expandContext and chunks:
            chunks = await self.expand_context(chunks, self.config.contextWindowSize)

        return RetrievalResult(
            chunks=chunks,
            query_analysis=analysis,
            total_candidates=len(results),
            filtered=len(chunks),
            retrieval_method='semantic'
        )

    async def retrieve_with_fallback(
        self,
        query: str,
        filters: Optional[dict] = None,
        top_k: Optional[int] = None
    ) -> RetrievalResult:
        effective_top_k = top_k or self.config.topK
        result = await self.retrieve(query, filters, effective_top_k)

        # If enough results, return
        if len(result.chunks) >= 3:
            return result

        print(f"⚠️ Only {len(result.chunks)} chunks found, trying fallback threshold...")

        query_embedding = await self.embedder.embed_query(query)
        candidate_count = effective_top_k * 3
        results = await self.db.similarity_search(query_embedding, candidate_count, filters)
        boosted_results = self.apply_smart_boosting(results, result.queryAnalysis)

        # Fallback threshold
        fallback_filtered = [r for r in boosted_results if r["boostedScore"] >= self.config.fallbackThreshold]
        if len(fallback_filtered) >= 2:
            diverse = self.apply_diversity_reranking(fallback_filtered, effective_top_k)
            chunks = [self.format_chunk(r, 'semantic') for r in diverse]

            if self.config.expandContext and chunks:
                chunks = await self.expand_context(chunks, self.config.contextWindowSize)

            return RetrievalResult(
                chunks=chunks,
                query_analysis=result.queryAnalysis,
                total_candidates=len(results),
                filtered=len(chunks),
                retrieval_method='semantic'
            )

        # Try minimum threshold
        print('⚠️ Fallback threshold yielded few results, trying minimum threshold...')
        fallback_filtered = [r for r in boosted_results if r["boostedScore"] >= self.config.minimumThreshold]
        if len(fallback_filtered) >= 1:
            diverse = self.apply_diversity_reranking(fallback_filtered, effective_top_k)
            chunks = [self.format_chunk(r, 'semantic') for r in diverse]

            if self.config.expandContext and chunks:
                chunks = await self.expand_context(chunks, self.config.contextWindowSize)

            return RetrievalResult(
                chunks=chunks,
                query_analysis=result.queryAnalysis,
                total_candidates=len(results),
                filtered=len(chunks),
                retrieval_method='semantic'
            )

        # Keyword fallback
        if self.config.useKeywordFallback:
            print('🔤 Semantic search yielded no results, trying keyword search...')
            key_terms = self.extract_key_terms(query)
            print(f"   Key terms: {', '.join(key_terms)}")

            if key_terms:
                kw_results = await self.keyword_search(key_terms, effective_top_k, filters)
                if kw_results:
                    boosted_kw = self.apply_smart_boosting(kw_results, result.queryAnalysis)
                    chunks = [self.format_chunk(r, 'keyword') for r in boosted_kw]

                    if self.config.expandContext and chunks:
                        chunks = await self.expand_context(chunks, self.config.contextWindowSize)

                    return RetrievalResult(
                        chunks=chunks,
                        query_analysis=result.queryAnalysis,
                        total_candidates=len(kw_results),
                        filtered=len(chunks),
                        retrieval_method='keyword'
                    )

        # Last resort
        print('❌ All retrieval methods exhausted, returning best available results')
        any_results = boosted_results[:effective_top_k]
        chunks = [self.format_chunk(r, 'semantic') for r in any_results]
        
        return RetrievalResult(
            chunks=chunks,
            query_analysis=result.queryAnalysis,
            total_candidates=len(results),
            filtered=len(chunks),
            retrieval_method='semantic'
        )

    def apply_smart_boosting(self, results: List[dict], analysis: QueryAnalysis) -> List[dict]:
        boosted = []
        for row in results:
            similarity = row["similarity"]
            meta = row.get("metadata") or {}
            factors = analysis.boostFactors
            boost = 1.0

            el_type = meta.get("elementType")
            
            # Element Type Boosts
            if el_type == ElementType.TABLE.value:
                boost *= factors.get("tableBoost", 1.0)
            elif el_type == ElementType.LIST.value:
                boost *= factors.get("listBoost", 1.0)
            elif el_type == ElementType.CODE_BLOCK.value:
                boost *= factors.get("codeBoost", 1.0)
            elif el_type == ElementType.HEADER.value:
                boost *= factors.get("headerBoost", 1.0)
            elif el_type == ElementType.PARAGRAPH.value:
                boost *= factors.get("paragraphBoost", 1.0)

            # Preferred elements boosts
            preferred_vals = [t.value if isinstance(t, ElementType) else t for t in analysis.preferredElementTypes]
            if el_type in preferred_vals:
                idx = preferred_vals.index(el_type)
                boost *= 1.0 + (0.1 * (len(preferred_vals) - idx))

            # Characteristics boosts
            if meta.get("containsNumbers") or meta.get("hasNumericData"):
                boost *= factors.get("numericContentBoost", 1.0)
            if meta.get("hasDefinitions"):
                boost *= factors.get("definitionBoost", 1.0)
            if meta.get("hasExamples"):
                boost *= factors.get("exampleBoost", 1.0)

            # Required metadata check
            req = analysis.requiredMetadata
            if req.get("mustHaveNumbers") and not meta.get("containsNumbers") and not meta.get("hasNumericData"):
                boost *= 0.7
            if req.get("mustHaveCode") and el_type != ElementType.CODE_BLOCK.value:
                boost *= 0.8

            if meta.get("searchBoost"):
                boost *= float(meta["searchBoost"])

            boosted.append({
                **row,
                "metadata": meta,
                "similarity": similarity,
                "boostedScore": similarity * boost
            })
        
        # Sort by boostedScore
        boosted.sort(key=lambda x: x["boostedScore"], reverse=True)
        return boosted

    def apply_diversity_reranking(self, results: List[dict], top_k: int) -> List[dict]:
        if len(results) <= top_k:
            return results

        selected = []
        remaining = list(results)

        while len(selected) < top_k and remaining:
            best = remaining.pop(0)
            selected.append(best)

            for item in remaining:
                is_same_doc = item["doc_id"] == best["doc_id"]
                is_same_sec = item["metadata"].get("section") == best["metadata"].get("section")
                is_nearby = abs(item["chunk_index"] - best["chunk_index"]) <= 2

                if is_same_doc and (is_same_sec or is_nearby):
                    item["boostedScore"] *= (1 - self.config.diversityFactor)

            remaining.sort(key=lambda x: x["boostedScore"], reverse=True)

        return selected

    def format_chunk(self, row: dict, match_type: str = 'semantic') -> RetrievedChunk:
        return RetrievedChunk(
            id=row["id"],
            docId=row["doc_id"],
            docName=row["doc_name"],
            docType=row["doc_type"],
            chunkIndex=row["chunk_index"],
            content=row["content"],
            similarity=row["similarity"],
            boostedScore=row["boostedScore"],
            metadata=row["metadata"],
            matchType=row.get("matchType", match_type)
        )

    def get_default_analysis(self, query: str) -> QueryAnalysis:
        return QueryAnalysis(
            originalQuery=query,
            queryType=QueryType.FACTUAL,
            preferredElementTypes=[ElementType.PARAGRAPH],
            requiredMetadata={},
            boostFactors={
                "tableBoost": 1.0,
                "listBoost": 1.0,
                "paragraphBoost": 1.0,
                "codeBoost": 1.0,
                "headerBoost": 1.0,
                "numericContentBoost": 1.0,
                "definitionBoost": 1.0,
                "exampleBoost": 1.0
            }
        )

    async def expand_context(self, chunks: List[RetrievedChunk], window_size: int = 2) -> List[RetrievedChunk]:
        if not chunks or not self.config.expandContext:
            return chunks

        print(f"🔄 Expanding context with window size {window_size} for {len(chunks)} chunks...")

        # Group by doc id
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
                query = """
                    SELECT id, doc_id, doc_name, doc_type, chunk_index, content, metadata,
                           0.5 AS similarity
                    FROM documents
                    WHERE doc_id = $1 AND chunk_index = ANY($2::int[])
                    ORDER BY chunk_index ASC
                """
                rows = await self.db.query(query, doc_id, indices)

                for row in rows:
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

        # Sort by docId and chunkIndex
        expanded.sort(key=lambda x: (x.docId, x.chunkIndex))
        print(f"✅ Context expansion: {len(chunks)} → {len(expanded)} chunks")
        return expanded

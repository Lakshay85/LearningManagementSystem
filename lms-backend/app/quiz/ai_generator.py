import sys
import json
import re
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import text
from app.config import settings
from app.database import AsyncSessionLocal
from app.llm.providers import LLMProviderManager

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

logger = logging.getLogger(__name__)

class QuizAIGenerator:
    def __init__(self):
        self._llm_manager = None

    @property
    def llm_manager(self):
        if self._llm_manager is None:
            self.api_key = settings.GROQ_API_KEY
            self.model = settings.GROQ_MODEL or "llama-3.3-70b-versatile"
            primary_config = {
                "provider": "groq",
                "apiKey": self.api_key,
                "model": self.model,
                "temperature": 0.5,
                "maxTokens": 4096,
            }
            self._llm_manager = LLMProviderManager(primary_config)
        return self._llm_manager


    async def _fetch_document_chunks(self, document_ids: List[str], max_chunks: int = 15) -> List[str]:
        """Fetch chunks from rag_documents for specific document IDs."""
        if not document_ids:
            return []
            
        async with AsyncSessionLocal() as session:
            query = text("""
                SELECT content FROM rag_documents
                WHERE doc_id = ANY(:doc_ids)
                ORDER BY chunk_index ASC
                LIMIT :limit
            """)
            result = await session.execute(query, {
                "doc_ids": document_ids,
                "limit": max_chunks
            })
            rows = result.fetchall()
            return [row[0] for row in rows if row[0]]

    async def _fetch_course_chunks(self, course_id: str, max_chunks: int = 15) -> List[str]:
        """Fetch chunks associated with a course from rag_documents."""
        async with AsyncSessionLocal() as session:
            # Query documents attached to this course via course_contents or metadata
            query = text("""
                SELECT rd.content 
                FROM rag_documents rd
                WHERE rd.doc_id IN (
                    SELECT "documentId"::text FROM course_contents 
                    WHERE "courseId" = :course_id AND "documentId" IS NOT NULL
                )
                OR (rd.metadata->>'courseId' = :course_id_str)
                LIMIT :limit
            """)
            result = await session.execute(query, {
                "course_id": course_id,
                "course_id_str": str(course_id),
                "limit": max_chunks
            })
            rows = result.fetchall()
            return [row[0] for row in rows if row[0]]

    async def generate_questions(
        self,
        course_title: str,
        num_questions: int = 10,
        difficulty: str = "medium",
        topic: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        course_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple-choice quiz questions using Groq LLM.
        Optionally utilizes uploaded document context from RAG.
        """
        context_chunks: List[str] = []
        if document_ids:
            context_chunks = await self._fetch_document_chunks(document_ids)
        elif course_id:
            context_chunks = await self._fetch_course_chunks(course_id)

        context_text = ""
        if context_chunks:
            joined = "\n\n---\n\n".join(context_chunks[:12])
            context_text = f"\n\nREFERENCE COURSE MATERIAL:\n{joined}\n"

        prompt = f"""You are an expert professor and assessment designer for the course "{course_title}".
Your task is to generate {num_questions} high-quality multiple choice questions.

Parameters:
- Number of Questions: {num_questions}
- Difficulty Level: {difficulty}
- Specific Topic/Focus: {topic if topic else "General course syllabus and reference material"}
{context_text}
CRITICAL REQUIREMENTS:
1. Every question must have EXACTLY 4 distinct, plausible options.
2. The `correctAnswer` must be an EXACT string match to one of the 4 options.
3. Include an insightful, educational `explanation` detailing why the correct answer is right.
4. If reference material is provided above, generate questions grounded in that material.
5. Return ONLY a valid JSON array of objects. Do NOT include markdown code fences, headers, or any commentary.

JSON Format:
[
  {{
    "questionText": "What is the primary characteristic of...",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correctAnswer": "Option A",
    "explanation": "Option A is correct because..."
  }}
]
"""

        try:
            # Each question with 4 options + explanation needs ~200-250 tokens
            token_budget = max(3000, num_questions * 250)
            response = await self.llm_manager.generate(prompt, {
                "maxTokens": token_budget,
                "temperature": 0.4
            })
            raw_text = response.content.strip()
            logger.info(f"AI response length: {len(raw_text)} chars")
            
            # Extract JSON block
            parsed_questions = self._parse_json_response(raw_text)
            
            # Normalize and validate questions
            validated = []
            for i, q in enumerate(parsed_questions):
                q_text = q.get("questionText") or q.get("question")
                opts = q.get("options")
                ans = q.get("correctAnswer") or q.get("answer")
                explanation = q.get("explanation", "")

                if not q_text or not opts or not isinstance(opts, list) or len(opts) < 2:
                    continue

                # Ensure 4 options if possible
                opts_cleaned = [str(o).strip() for o in opts]
                if len(opts_cleaned) > 4:
                    opts_cleaned = opts_cleaned[:4]
                while len(opts_cleaned) < 4:
                    opts_cleaned.append(f"Option {chr(65 + len(opts_cleaned))}")

                ans_str = str(ans).strip() if ans else opts_cleaned[0]
                # If ans is just a letter like 'A' or 'B'
                if ans_str in ['A', 'B', 'C', 'D'] and len(opts_cleaned) >= 4:
                    idx = ord(ans_str) - ord('A')
                    ans_str = opts_cleaned[idx]
                elif ans_str not in opts_cleaned:
                    # Match case-insensitively or default to first
                    matched = False
                    for opt in opts_cleaned:
                        if ans_str.lower() == opt.lower():
                            ans_str = opt
                            matched = True
                            break
                    if not matched:
                        opts_cleaned[0] = ans_str

                validated.append({
                    "questionText": str(q_text).strip(),
                    "options": opts_cleaned,
                    "correctAnswer": ans_str,
                    "explanation": str(explanation).strip() if explanation else None,
                    "order": i,
                    "points": 1
                })

            if not validated:
                raise ValueError("Failed to parse valid questions from AI response")

            logger.info(f"Successfully parsed {len(validated)} questions")
            return validated[:num_questions]

        except Exception as e:
            logger.error(f"Error in QuizAIGenerator: {str(e)}")
            raise e

    def _parse_json_response(self, text: str) -> List[Dict[str, Any]]:
        """Robustly extract and parse JSON array from LLM response text.
        
        Handles: markdown fences, truncated responses, wrapper objects,
        chatty preambles, and malformed trailing commas.
        """
        # ── Step 1: Strip markdown code fences ──
        clean = re.sub(r'```(?:json)?\s*', '', text).strip()
        clean = clean.rstrip('`').strip()

        # ── Step 2: Try direct parse (ideal case) ──
        for candidate in [clean, text.strip()]:
            try:
                data = json.loads(candidate)
                if isinstance(data, list):
                    return data
                if isinstance(data, dict) and "questions" in data:
                    return data["questions"]
            except (json.JSONDecodeError, ValueError):
                pass

        # ── Step 3: Extract bracket-delimited JSON array ──
        start = clean.find('[')
        if start != -1:
            end = clean.rfind(']')
            if end > start:
                fragment = clean[start:end + 1]
                try:
                    data = json.loads(fragment)
                    if isinstance(data, list):
                        return data
                except (json.JSONDecodeError, ValueError):
                    # Try fixing trailing commas before ]
                    fixed = re.sub(r',\s*\]', ']', fragment)
                    try:
                        data = json.loads(fixed)
                        if isinstance(data, list):
                            return data
                    except (json.JSONDecodeError, ValueError):
                        pass

            # ── Step 4: Handle TRUNCATED JSON (no closing ]) ──
            # The LLM ran out of tokens mid-array. Try to salvage complete objects.
            fragment = clean[start:]
            # Find the last complete object by looking for the last '}' followed
            # by optional whitespace/comma but NOT another '{'
            last_brace = fragment.rfind('}')
            if last_brace > 0:
                # Try progressively shorter suffixes to find valid JSON
                attempt = fragment[:last_brace + 1].rstrip().rstrip(',').strip()
                if not attempt.endswith(']'):
                    attempt += ']'
                # Fix trailing commas
                attempt = re.sub(r',\s*\]', ']', attempt)
                try:
                    data = json.loads(attempt)
                    if isinstance(data, list):
                        logger.warning(f"Recovered {len(data)} questions from truncated JSON response")
                        return data
                except (json.JSONDecodeError, ValueError):
                    pass

        # ── Step 5: Extract individual JSON objects via regex ──
        # Last resort: find all {...} blocks that look like question objects
        obj_pattern = re.compile(
            r'\{[^{}]*"(?:questionText|question)"[^{}]*"(?:options)"[^{}]*\[.*?\][^{}]*\}',
            re.DOTALL
        )
        objects = []
        for m in obj_pattern.finditer(clean):
            try:
                obj = json.loads(m.group(0))
                if isinstance(obj, dict):
                    objects.append(obj)
            except (json.JSONDecodeError, ValueError):
                pass

        if objects:
            logger.warning(f"Recovered {len(objects)} questions via individual object extraction")
            return objects

        raise ValueError(f"Could not parse valid JSON array from AI response: {text[:300]}...")

quiz_ai_generator = QuizAIGenerator()

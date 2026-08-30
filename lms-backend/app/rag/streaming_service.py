import json
import asyncio
import time
import os
from typing import AsyncGenerator, Optional, Dict, Any

from app.config import settings
from app.rag.db_service import rag_db_service
from app.chat.service import chat_memory_service
from app.rag.ingestion.embedder import Embedder
from app.rag.structure.smart_retriever import SmartRetriever
from app.llm.providers import LLMProviderManager

from app.intent.service import (
    intent_detection_service,
    response_generator_service,
    conversation_context_service
)
from app.intent.types import (
    QueryIntent,
    CONVERSATIONAL_INTENTS
)

class RagStreamingService:
    def __init__(self):
        self.chat_memory = chat_memory_service
        self.db = rag_db_service

        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            print("⚠️ GROQ_API_KEY is not set")

        primary_config = {
            "provider": "groq",
            "apiKey": self.api_key,
            "model": settings.GROQ_MODEL or "qwen/qwen3.8-27b",
            "temperature": 0.4,
            "maxTokens": 2048,
            "streaming": True
        }
        self.llm_manager = LLMProviderManager(primary_config)

        self.embedder = Embedder.create_from_env()
        self.smart_retriever = SmartRetriever(self.db, self.embedder, {
            "topK": int(os.getenv("TOP_K", "20")),
            "similarityThreshold": float(os.getenv("SIMILARITY_THRESHOLD", "0.25")),
            "fallbackThreshold": float(os.getenv("FALLBACK_SIMILARITY_THRESHOLD", "0.15")),
            "minimumThreshold": 0.10,
            "useQueryAnalysis": True,
            "diversityFactor": 0.05,
            "useKeywordFallback": True,
            "expandContext": True,
            "contextWindowSize": int(os.getenv("CONTEXT_WINDOW_SIZE", "2"))
        })

        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.30"))
        self.min_context_length = int(os.getenv("MIN_CONTEXT_LENGTH", "50"))
        self.min_query_words_for_refinement = int(os.getenv("MIN_QUERY_WORDS_FOR_REFINEMENT", "4"))
        self.summary_interval = 10

        self.use_intent_detection = os.getenv("USE_INTENT_DETECTION", "true").lower() != "false"
        self.intent_detector = intent_detection_service
        self.response_generator = response_generator_service
        self.context_service = conversation_context_service

        print("🚀 RAG Streaming Service initialized")

    async def close(self):
        await self.db.close()

    async def query_stream(
        self,
        query: str,
        filters: Optional[dict] = None,
        top_k: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        
        def format_sse(event_type: str, data: dict) -> str:
            return f"data: {json.dumps({'type': event_type, **data})}\n\n"

        filters = filters or {}
        session_id = filters.get("sessionId")
        full_response = ""

        try:
            print(f"\n{'='*60}")
            print("🔍 RAG Streaming Query Started")
            print(f"📝 Query: \"{query}\"")

            # Persist user message
            if session_id:
                try:
                    await self.chat_memory.add_message(
                        session_id=session_id,
                        role="user",
                        content=query
                    )
                    print(f"💾 User message saved to session: {session_id}")
                except Exception as err:
                    print(f"⚠️ Failed to save user message: {str(err)}")

            # Step 1: Intent Detection
            yield format_sse("status", {"message": "Analyzing your question..."})

            if self.use_intent_detection and self.intent_detector:
                try:
                    intent_res = await self.intent_detector.classify_intent(query, session_id)
                    intent = intent_res.get("intent")
                    print(f"🎯 Intent: {intent}")

                    if intent in [c.value for c in CONVERSATIONAL_INTENTS]:
                        yield format_sse("status", {"message": "Generating response..."})

                        response = await self.response_generator.generate_response(
                            intent=QueryIntent(intent),
                            query=query,
                            session_id=session_id
                        )

                        for char in response:
                            yield format_sse("chunk", {"text": char})
                            full_response += char
                            await asyncio.sleep(0.01)

                        await self.persist_assistant_message(session_id, full_response)
                        yield format_sse("done", {"success": True})
                        return

                except Exception as err:
                    print(f"⚠️ Intent detection failed: {str(err)}")

            # Step 2: Query Refinement
            yield format_sse("status", {"message": "Refining query for better results..."})

            refined_query = query
            query_words = len(query.strip().split())

            if query_words >= self.min_query_words_for_refinement:
                try:
                    refined_query = await self.refining_query(query)
                    print(f"🔧 Refined: \"{refined_query}\"")
                except Exception as err:
                    print(f"⚠️ Refinement failed: {str(err)}")

            # Step 3: Smart Retrieval
            yield format_sse("status", {"message": "Searching course materials..."})
            
            effective_top_k = top_k or int(os.getenv("TOP_K", "10"))
            doc_filters = self.extract_document_filters(filters)

            retrieval_res = await self.smart_retriever.retrieve_with_fallback(
                query=refined_query,
                filters=doc_filters,
                top_k=effective_top_k
            )

            print(f"✅ Retrieved {len(retrieval_res.chunks)} chunks")

            if not retrieval_res.chunks:
                no_res = "I couldn't find relevant information in the course materials to answer your question."
                for char in no_res:
                    yield format_sse("chunk", {"text": char})
                    full_response += char
                    await asyncio.sleep(0.01)

                await self.persist_assistant_message(session_id, full_response)
                yield format_sse("done", {"success": True})
                return

            # Step 4: Build Context
            context_parts = []
            for idx, chunk in enumerate(retrieval_res.chunks):
                context_parts.append(f"Source {idx + 1} [{chunk.docName}]:\n{chunk.content.strip()}")
            context = "\n\n---\n\n".join(context_parts)

            if len(context) < self.min_context_length:
                short_ctx = "I don't have enough information to answer this question. Please consult your teacher."
                for char in short_ctx:
                    yield format_sse("chunk", {"text": char})
                    full_response += char
                    await asyncio.sleep(0.01)

                await self.persist_assistant_message(session_id, full_response)
                yield format_sse("done", {"success": True})
                return

            # Step 5: Stream LLM Response
            yield format_sse("status", {"message": "Generating response..."})
            prompt = self.build_prompt(query, context)
            print("📝 Starting streaming generation...")

            async for chunk in self.llm_manager.generate_stream(prompt):
                if chunk.content:
                    yield format_sse("chunk", {"text": chunk.content})
                    full_response += chunk.content

            print("✅ Streaming complete")
            await self.persist_assistant_message(session_id, full_response)
            yield format_sse("done", {"success": True})

        except Exception as e:
            print(f"❌ Streaming error: {str(e)}")
            if full_response and session_id:
                try:
                    await self.persist_assistant_message(session_id, full_response)
                except Exception:
                    pass
            yield format_sse("error", {"message": str(e) or "An error occurred"})

    async def persist_assistant_message(self, session_id: Optional[str], content: str):
        if not session_id or not content:
            return

        try:
            await self.chat_memory.add_message(
                session_id=session_id,
                role="assistant",
                content=content
            )
            print(f"💾 Assistant message saved to session: {session_id}")
            
            asyncio.create_task(self.trigger_summarization_if_needed(session_id))
        except Exception as err:
            print(f"⚠️ Failed to save assistant message: {str(err)}")

    async def trigger_summarization_if_needed(self, session_id: str):
        try:
            session = await self.chat_memory.get_session(session_id)
            if not session:
                return

            msg_cnt = session.messageCount if hasattr(session, "messageCount") else session.get("messageCount", 0)
            if msg_cnt < self.summary_interval or msg_cnt % self.summary_interval != 0:
                return

            print(f"📊 Generating conversation summary for session {session_id} ({msg_cnt} messages)")

            messages = await self.chat_memory.get_session_messages(session_id, 50)
            existing_summary = session.summary if hasattr(session, "summary") else session.get("summary", "")

            formatted = []
            for m in messages:
                role_val = m.role if hasattr(m, "role") else m.get("role", "")
                if role_val != "system":
                    lbl = "Student" if role_val == "user" else "Assistant"
                    content_val = m.content if hasattr(m, "content") else m.get("content", "")
                    formatted.append(f"{lbl}: {content_val}")

            conv_text = "\n".join(formatted)

            summary_prompt = f"""You are a conversation summarizer for a Learning Management System.

Create a concise summary of the following student-assistant conversation. The summary should:
- Capture the key topics discussed and questions asked
- Note any important answers or explanations given
- Preserve the context needed to continue the conversation naturally
- Be 3-5 sentences maximum

{f'PREVIOUS SUMMARY:{existing_summary}' if existing_summary else ''}
CONVERSATION:
{conv_text}

CONCISE SUMMARY:"""

            response = await self.llm_manager.generate(summary_prompt)
            summary_text = response.content.strip()
            
            await self.chat_memory.update_session_summary(session_id, summary_text)
            print(f"✅ Summary updated for session {session_id}")

        except Exception as e:
            print(f"❌ Summary generation failed: {str(e)}")

    async def refining_query(self, query: str) -> str:
        prompt = f"""You are a query refinement assistant for a Learning Management System.
Transform the user's input into a clear, precise, and searchable query.

RULES:
- Do NOT answer the question.
- Do NOT add new concepts.
- Output only the refined query as a single line.

Original query: {query}

Refined query:"""

        response = await self.llm_manager.generate(prompt)
        return response.content.strip()

    def build_prompt(self, query: str, context: str) -> str:
        return f"""You are an intelligent teaching assistant for a Learning Management System.
Help students understand concepts using the provided course materials.

INSTRUCTIONS:
- Use the context as your PRIMARY source.
- Explain concepts in your own words.
- Keep the tone friendly and educational.
- If the context doesn't have relevant info, say so politely.
- Do NOT invent facts.

CONTEXT FROM COURSE MATERIALS:
{context}

STUDENT'S QUESTION: {query}

YOUR ANSWER:"""

    def extract_document_filters(self, filters: dict) -> Optional[dict]:
        if not filters:
            return None

        non_doc_keys = ["sessionId", "userId", "topK", "stream", "temperature"]
        doc_filters = {}
        has_filters = False

        for k, v in filters.items():
            if k not in non_doc_keys and v is not None:
                doc_filters[k] = v
                has_filters = True

        return doc_filters if has_filters else None

# Singleton service instance
rag_streaming_service = RagStreamingService()

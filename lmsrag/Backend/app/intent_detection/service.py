import os
import re
import time
import random
import uuid
from typing import List, Dict, Any, Tuple, Optional
from groq import AsyncGroq

from app.config import settings
from app.intent_detection.types import (
    QueryIntent,
    ConfidenceLevel,
    DEFAULT_INTENT_DETECTION_CONFIG,
    DEFAULT_CACHE_CONFIG,
    DEFAULT_CONTEXT_CONFIG,
    DEFAULT_RESPONSE_CONFIG,
    CONVERSATIONAL_INTENTS,
    RETRIEVAL_INTENTS
)

CLASSIFICATION_PROMPT = """You are an intent classifier for a Learning Management System's AI assistant.
Analyze the user's message and classify it into one of these intents:

INTENTS:
- greeting: User is saying hello, hi, hey, good morning, etc.
- gratitude: User is expressing thanks, appreciation, etc.
- farewell: User is saying goodbye, bye, see you, etc.
- clarification: User is asking for clarification about a previous response
- follow_up: User is asking a follow-up question referencing previous context (e.g., "tell me more", "what about...", "and what is...")
- question: User is asking a genuine educational question that needs information retrieval
- out_of_scope: User is asking about something unrelated to education (e.g., booking flights, personal advice, weather)

RULES:
1. Short ambiguous messages like "ok", "yes", "no" should be classified based on likely context
2. Questions about courses, topics, concepts, explanations are "question"
3. "What is X", "Explain Y", "How does Z work" are questions
4. References to "that", "this", "it" without clear context are often follow_ups
5. Be confident in classification - most messages have clear intent

Respond ONLY with a JSON object in this exact format:
{"intent": "<intent_name>", "confidence": <0.0-1.0>, "reasoning": "<brief explanation>"}

User message: "{query}"

JSON response:"""

INTENT_PROMPTS = {
    QueryIntent.GREETING: """You are a friendly and helpful teaching assistant for a Learning Management System.
The student has greeted you. Respond warmly and offer to help with their course-related questions.
Keep the response brief (1-2 sentences), friendly, and professional.
Do NOT mention that you are an AI or have limitations.

Student's message: {query}

Your warm greeting:""",

    QueryIntent.GRATITUDE: """You are a friendly teaching assistant for a Learning Management System.
The student is thanking you. Acknowledge their thanks warmly and offer to help with anything else.
Keep the response brief (1-2 sentences) and encouraging.

Student's message: {query}

Your response:""",

    QueryIntent.FAREWELL: """You are a friendly teaching assistant for a Learning Management System.
The student is saying goodbye. Respond politely, wish them well with their studies, and invite them to return.
Keep it brief (1-2 sentences).

Student's message: {query}

Your farewell:""",

    QueryIntent.OUT_OF_SCOPE: """You are a teaching assistant for a Learning Management System focused on course materials and educational content.
The student has asked about something outside your capabilities (like booking, transactions, personal advice, etc.).
Politely explain that you can only help with course-related questions and materials.
Suggest they contact the appropriate service or try asking about course topics.
Keep it brief and helpful.

Student's request: {query}

Your polite redirect:""",

    QueryIntent.EMPTY: "Respond with a brief, helpful message asking the student what they would like to know about their courses.",
    
    QueryIntent.TOO_LONG: "The query was too long. Respond briefly asking the student to shorten their question.",
    
    QueryIntent.CLARIFICATION: """You are a teaching assistant. The student needs clarification.
Based on the conversation context, ask a specific clarifying question to understand what they need.

{context}
Current message: {query}

Your clarifying question:""",
    
    QueryIntent.FOLLOW_UP: "",
    QueryIntent.QUESTION: ""
}

FALLBACK_RESPONSES = {
    QueryIntent.GREETING: [
        "Hello! 👋 How can I help you with your course materials today?",
        "Hi there! I'm here to help you with your studies. What would you like to know?",
        "Welcome! Feel free to ask me anything about your courses.",
    ],
    QueryIntent.GRATITUDE: [
        "You're welcome! Let me know if you have any other questions.",
        "Happy to help! Feel free to ask if you need anything else.",
        "Glad I could assist! Don't hesitate to reach out again.",
    ],
    QueryIntent.FAREWELL: [
        "Goodbye! Good luck with your studies! 📚",
        "See you later! Feel free to come back anytime.",
        "Take care! Wishing you success in your learning journey.",
    ],
    QueryIntent.OUT_OF_SCOPE: [
        "I'm designed to help with course-related questions. Could you ask me something about your study materials?",
        "That's outside my area of expertise. I can help you with questions about your courses and learning materials.",
        "I specialize in educational content. Try asking me about topics from your courses!",
    ],
    QueryIntent.EMPTY: [
        "I didn't catch that. What would you like to know about your courses?",
        "Please type your question and I'll do my best to help!",
    ],
    QueryIntent.TOO_LONG: [
        "Your question is quite long. Could you summarize what you'd like to know?",
        "Please try asking a shorter, more focused question so I can help you better.",
    ],
    QueryIntent.CLARIFICATION: [
        "Could you please clarify what you'd like to know?",
    ],
    QueryIntent.FOLLOW_UP: [],
    QueryIntent.QUESTION: []
}

# ==================== Cache Service ====================

class CacheEntry:
    def __init__(self, classification: dict, created_at: float, hit_count: int = 0):
        self.classification = classification
        self.createdAt = created_at
        self.hitCount = hit_count

class IntentCacheService:
    def __init__(self):
        self.cache: Dict[str, CacheEntry] = {}
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
        self.config = {
            "ttlMs": int(os.getenv("INTENT_CACHE_TTL_MS", str(DEFAULT_CACHE_CONFIG["ttlMs"]))),
            "maxSize": int(os.getenv("INTENT_CACHE_MAX_SIZE", str(DEFAULT_CACHE_CONFIG["maxSize"]))),
            "enabled": os.getenv("INTENT_CACHE_ENABLED", "true").lower() != "false"
        }

    def normalize_key(self, query: str) -> str:
        return re.sub(r"\s+", " ", query.lower().strip())[:500]

    def get(self, query: str) -> Optional[dict]:
        if not self.config["enabled"]:
            return None

        key = self.normalize_key(query)
        entry = self.cache.get(key)

        if not entry:
            self.stats["misses"] += 1
            return None

        # Expiry check (ms conversion)
        if (time.time() * 1000) - entry.createdAt > self.config["ttlMs"]:
            self.cache.pop(key, None)
            self.stats["misses"] += 1
            return None

        entry.hitCount += 1
        self.stats["hits"] += 1
        return {
            **entry.classification,
            "fromCache": True
        }

    def set(self, query: str, classification: dict):
        if not self.config["enabled"]:
            return

        key = self.normalize_key(query)

        # Evict if full
        if len(self.cache) >= self.config["maxSize"] and key not in self.cache:
            self.evict_lru()

        self.cache[key] = CacheEntry(
            classification={**classification, "fromCache": False},
            created_at=time.time() * 1000,
            hit_count=0
        )

    def evict_lru(self):
        if not self.cache:
            return

        lru_key = None
        lru_entry = None

        for key, entry in self.cache.items():
            if not lru_entry:
                lru_key = key
                lru_entry = entry
                continue

            if (entry.hitCount < lru_entry.hitCount) or \
               (entry.hitCount == lru_entry.hitCount and entry.createdAt < lru_entry.createdAt):
                lru_key = key
                lru_entry = entry

        if lru_key:
            self.cache.pop(lru_key, None)
            self.stats["evictions"] += 1

    def cleanup_expired(self):
        now_ms = time.time() * 1000
        expired_keys = []
        for key, entry in self.cache.items():
            if now_ms - entry.createdAt > self.config["ttlMs"]:
                expired_keys.append(key)
        
        for key in expired_keys:
            self.cache.pop(key, None)
            
        if expired_keys:
            print(f"🧹 Cache cleanup: removed {len(expired_keys)} expired entries")

    def clear(self):
        self.cache.clear()
        print("🗑️ Cache cleared")

    def get_stats(self) -> dict:
        total = self.stats["hits"] + self.stats["misses"]
        return {
            "size": len(self.cache),
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "hitRate": self.stats["hits"] / total if total > 0 else 0.0
        }

# ==================== Context Service ====================

class ConversationMessage:
    def __init__(self, role: str, content: str, intent: Optional[QueryIntent] = None):
        self.id = str(uuid.uuid4())
        self.role = role
        self.content = content
        self.timestamp = time.time()
        self.intent = intent

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "intent": self.intent.value if isinstance(self.intent, QueryIntent) else self.intent
        }

class ConversationContext:
    def __init__(self, session_id: str):
        self.sessionId = session_id
        self.messages: List[ConversationMessage] = []
        self.lastActivityAt = time.time()

class ConversationContextService:
    def __init__(self):
        self.contexts: Dict[str, ConversationContext] = {}
        self.config = {
            "maxHistorySize": int(os.getenv("CONVERSATION_HISTORY_SIZE", str(DEFAULT_CONTEXT_CONFIG["maxHistorySize"]))),
            "sessionTimeoutMs": int(os.getenv("SESSION_TIMEOUT_MS", str(DEFAULT_CONTEXT_CONFIG["sessionTimeoutMs"])))
        }

    def get_or_create_context(self, session_id: str) -> ConversationContext:
        context = self.contexts.get(session_id)
        now = time.time()

        if not context:
            context = ConversationContext(session_id)
            self.contexts[session_id] = context
            print(f"📂 Created new conversation context for session: {session_id}")
        else:
            # Check timeout (convert timeout to seconds)
            if (now - context.lastActivityAt) * 1000 > self.config["sessionTimeoutMs"]:
                context = ConversationContext(session_id)
                self.contexts[session_id] = context
                print(f"♻️ Session expired, created fresh context for: {session_id}")
        return context

    def add_user_message(self, session_id: str, content: str, intent: Optional[QueryIntent] = None) -> ConversationMessage:
        context = self.get_or_create_context(session_id)
        msg = ConversationMessage(role="user", content=content, intent=intent)
        context.messages.append(msg)
        context.lastActivityAt = time.time()
        
        self.enforce_history_limit(context)
        return msg

    def add_assistant_message(self, session_id: str, content: str) -> ConversationMessage:
        context = self.get_or_create_context(session_id)
        msg = ConversationMessage(role="assistant", content=content)
        context.messages.append(msg)
        context.lastActivityAt = time.time()
        
        self.enforce_history_limit(context)
        return msg

    def get_recent_messages(self, session_id: str, count: Optional[int] = None) -> List[ConversationMessage]:
        context = self.contexts.get(session_id)
        if not context:
            return []

        if count and count < len(context.messages):
            return context.messages[-count:]
        return list(context.messages)

    def get_last_user_question(self, session_id: str) -> Optional[ConversationMessage]:
        context = self.contexts.get(session_id)
        if not context:
            return None

        for msg in reversed(context.messages):
            if msg.role == "user" and (msg.intent == QueryIntent.QUESTION or msg.intent == "question"):
                return msg
        return None

    def build_context_summary(self, session_id: str, max_messages: int = 6) -> str:
        messages = self.get_recent_messages(session_id, max_messages)
        if not messages:
            return ""

        formatted = []
        for msg in messages:
            role = "Student" if msg.role == "user" else "Assistant"
            formatted.append(f"{role}: {msg.content}")

        return f"Previous conversation:\n{chr(10).join(formatted)}\n---\n"

    def is_likely_follow_up(self, session_id: str, query: str) -> bool:
        context = self.contexts.get(session_id)
        if not context or len(context.messages) < 2:
            return False

        lowercase_query = query.lower()
        follow_up_indicators = [
            'more about', 'tell me more', 'what about', 'how about',
            'and what', 'can you explain', 'what else', 'anything else',
            'continue', 'go on', 'elaborate', 'expand on',
            'that', 'this', 'it', 'those', 'these'
        ]
        return any(indicator in lowercase_query for indicator in follow_up_indicators)

    def enforce_history_limit(self, context: ConversationContext):
        max_size = self.config["maxHistorySize"]
        if len(context.messages) > max_size:
            context.messages = context.messages[-max_size:]

    def cleanup_expired_sessions(self):
        now = time.time()
        cleaned = 0
        for session_id, context in list(self.contexts.items()):
            if (now - context.lastActivityAt) * 1000 > self.config["sessionTimeoutMs"]:
                self.contexts.pop(session_id, None)
                cleaned += 1
        if cleaned > 0:
            print(f"🧹 Cleaned up {cleaned} expired conversation sessions")

    def clear_session(self, session_id: str):
        self.contexts.pop(session_id, None)

    def get_active_session_count(self) -> int:
        return len(self.contexts)

# ==================== Response Generator Service ====================

class ResponseGeneratorService:
    def __init__(self, context_service: ConversationContextService):
        self.context_service = context_service
        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set")

        self.config = {
            "llmTemperature": float(os.getenv("RESPONSE_LLM_TEMPERATURE", str(DEFAULT_RESPONSE_CONFIG["llmTemperature"]))),
            "maxResponseTokens": int(os.getenv("RESPONSE_MAX_TOKENS", str(DEFAULT_RESPONSE_CONFIG["maxResponseTokens"])))
        }

        # Initialize Groq client
        self.llm = AsyncGroq(api_key=self.api_key)
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    async def generate_response(self
        , intent: QueryIntent
        , query: str
        , session_id: Optional[str] = None
    ) -> str:
        print(f"🎨 Generating response for intent: {intent}")

        # Empty or too long -> return fallback directly
        if intent == QueryIntent.EMPTY or intent == QueryIntent.TOO_LONG:
            return self.get_fallback_response(intent)

        try:
            prompt = self.build_prompt(intent, query, session_id)
            if not prompt:
                return self.get_fallback_response(intent)

            completion = await self.llm.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config["llmTemperature"],
                max_tokens=self.config["maxResponseTokens"]
            )
            text = completion.choices[0].message.content.strip()
            
            if text:
                print(f"✅ Generated response: \"{text[:100]}...\"")
                return text
            return self.get_fallback_response(intent)
        except Exception as e:
            print(f"❌ Response generation failed: {str(e)}")
            return self.get_fallback_response(intent)

    def build_prompt(self, intent: QueryIntent, query: str, session_id: Optional[str] = None) -> Optional[str]:
        template = INTENT_PROMPTS.get(intent)
        if not template:
            return None

        prompt = template.replace("{query}", query)

        if session_id and intent == QueryIntent.CLARIFICATION:
            ctx_summary = self.context_service.build_context_summary(session_id, 4)
            prompt = prompt.replace("{context}", ctx_summary)

        return prompt

    def get_fallback_response(self, intent: QueryIntent) -> str:
        res_list = FALLBACK_RESPONSES.get(intent)
        if not res_list:
            return "I'm here to help with your course questions. What would you like to know?"
        return random.choice(res_list)

    async def generate_out_of_scope_response(self, query: str, detected_domain: Optional[str] = None) -> str:
        domain_hint = f" (seems to be about {detected_domain})" if detected_domain else ""
        prompt = f"""You are a teaching assistant for a Learning Management System.
The student asked something outside your capabilities{domain_hint}.
Politely redirect them while being helpful.

Student's request: {query}

Your brief, helpful response:"""

        try:
            completion = await self.llm.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config["llmTemperature"],
                max_tokens=self.config["maxResponseTokens"]
            )
            text = completion.choices[0].message.content.strip()
            return text or self.get_fallback_response(QueryIntent.OUT_OF_SCOPE)
        except Exception:
            return self.get_fallback_response(QueryIntent.OUT_OF_SCOPE)

# ==================== Intent Detection Service ====================

class IntentDetectionService:
    def __init__(self, cache_service: IntentCacheService, context_service: ConversationContextService):
        self.cache_service = cache_service
        self.context_service = context_service
        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set")

        self.config = {
            "confidenceThreshold": float(os.getenv("INTENT_CONFIDENCE_THRESHOLD", str(DEFAULT_INTENT_DETECTION_CONFIG["confidenceThreshold"]))),
            "maxQueryLength": int(os.getenv("MAX_QUERY_LENGTH", str(DEFAULT_INTENT_DETECTION_CONFIG["maxQueryLength"]))),
            "useEmbeddingFallback": os.getenv("USE_EMBEDDING_FALLBACK", "true").lower() != "false",
            "llmTemperature": float(os.getenv("INTENT_LLM_TEMPERATURE", str(DEFAULT_INTENT_DETECTION_CONFIG["llmTemperature"]))),
            "maxClassificationTokens": int(os.getenv("INTENT_MAX_TOKENS", str(DEFAULT_INTENT_DETECTION_CONFIG["maxClassificationTokens"])))
        }

        self.llm = AsyncGroq(api_key=self.api_key)
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        print("🎯 Intent Detection Service initialized")

    async def classify_intent(self, query: str, session_id: Optional[str] = None) -> dict:
        start_time = time.time()

        # Step 1: Validate query
        validation = self.validate_query(query)
        if validation:
            validation["processingTimeMs"] = int((time.time() - start_time) * 1000)
            return validation

        normalized = query.strip()

        # Step 2: Check cache
        cached = self.cache_service.get(normalized)
        if cached:
            print(f"✅ Cache hit for intent: {cached['intent']}")
            cached["processingTimeMs"] = int((time.time() - start_time) * 1000)
            return cached

        # Step 3: Check conversation context
        if session_id and self.context_service.is_likely_follow_up(session_id, normalized):
            res = {
                "intent": QueryIntent.FOLLOW_UP.value,
                "confidence": 0.85,
                "confidenceLevel": ConfidenceLevel.HIGH.value,
                "reasoning": "Detected follow-up indicators with conversation context",
                "fromCache": False,
                "processingTimeMs": int((time.time() - start_time) * 1000)
            }
            self.cache_service.set(normalized, res)
            return res

        # Step 4: Classify with LLM
        try:
            classification = await self.classify_with_llm(normalized)
            self.cache_service.set(normalized, classification)
            
            classification["processingTimeMs"] = int((time.time() - start_time) * 1000)
            return classification
        except Exception as e:
            print(f"❌ LLM classification failed: {str(e)}")
            
            # Step 5: Fallback to heuristics
            fallback = self.fallback_classification(normalized)
            fallback["processingTimeMs"] = int((time.time() - start_time) * 1000)
            return fallback

    def validate_query(self, query: str) -> Optional[dict]:
        if not query or query.strip() == "":
            return {
                "intent": QueryIntent.EMPTY.value,
                "confidence": 1.0,
                "confidenceLevel": ConfidenceLevel.HIGH.value,
                "reasoning": "Empty or whitespace-only query",
                "fromCache": False,
                "processingTimeMs": 0
            }

        if len(query) > self.config["maxQueryLength"]:
            return {
                "intent": QueryIntent.TOO_LONG.value,
                "confidence": 1.0,
                "confidenceLevel": ConfidenceLevel.HIGH.value,
                "reasoning": f"Query exceeds maximum length of {self.config['maxQueryLength']} characters",
                "fromCache": False,
                "processingTimeMs": 0
            }
        return None

    async def classify_with_llm(self, query: str) -> dict:
        prompt = CLASSIFICATION_PROMPT.replace("{query}", query)
        print(f"🤖 Classifying intent via LLM: \"{query[:50]}...\"")

        completion = await self.llm.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config["llmTemperature"],
            max_tokens=self.config["maxClassificationTokens"]
        )
        response_text = completion.choices[0].message.content.strip()

        # Parse JSON
        parsed = self.parse_classification_response(response_text)
        
        intent = self.map_string_to_intent(parsed["intent"])
        confidence = min(1.0, max(0.0, parsed["confidence"]))
        confidence_level = self.get_confidence_level(confidence)

        print(f"🎯 Intent: {intent.value} (confidence: {confidence:.2f})")

        return {
            "intent": intent.value,
            "confidence": confidence,
            "confidenceLevel": confidence_level.value,
            "reasoning": parsed.get("reasoning", ""),
            "fromCache": False,
            "processingTimeMs": 0
        }

    def parse_classification_response(self, text: str) -> dict:
        try:
            # Match first JSON block {...}
            match = re.search(r"\{[\s\S]*\}", text)
            if not match:
                raise ValueError("No JSON block found")
            
            import json
            parsed = json.loads(match.group(0))
            return {
                "intent": parsed.get("intent", "question"),
                "confidence": parsed.get("confidence", 0.5),
                "reasoning": parsed.get("reasoning", "")
            }
        except Exception as e:
            print(f"Failed to parse LLM response: {text}, error: {str(e)}")
            return {
                "intent": "question",
                "confidence": 0.5,
                "reasoning": "Failed to parse LLM response, defaulting to question"
            }

    def map_string_to_intent(self, s: str) -> QueryIntent:
        mapping = {
            "greeting": QueryIntent.GREETING,
            "gratitude": QueryIntent.GRATITUDE,
            "farewell": QueryIntent.FAREWELL,
            "clarification": QueryIntent.CLARIFICATION,
            "follow_up": QueryIntent.FOLLOW_UP,
            "followup": QueryIntent.FOLLOW_UP,
            "question": QueryIntent.QUESTION,
            "out_of_scope": QueryIntent.OUT_OF_SCOPE,
            "outofscope": QueryIntent.OUT_OF_SCOPE
        }
        normalized = s.lower().replace('-', '_').replace(' ', '_')
        return mapping.get(normalized, QueryIntent.QUESTION)

    def get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        if confidence >= 0.85:
            return ConfidenceLevel.HIGH
        if confidence >= 0.7:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    def fallback_classification(self, query: str) -> dict:
        lower = query.lower().strip()

        # Greetings patterns
        greetings = r"^(hi|hello|hey|greetings|good\s*(morning|afternoon|evening)|howdy|hola)[\s!.,?]*$"
        if re.match(greetings, lower):
            return {
                "intent": QueryIntent.GREETING.value,
                "confidence": 0.9,
                "confidenceLevel": ConfidenceLevel.HIGH.value,
                "reasoning": "Matched greeting pattern (fallback)",
                "fromCache": False,
                "processingTimeMs": 0
            }

        # Gratitude patterns
        gratitude = r"^(thanks?|thank\s*you|thx|ty|appreciated?|cheers)[\s!.,?]*$"
        if re.match(gratitude, lower):
            return {
                "intent": QueryIntent.GRATITUDE.value,
                "confidence": 0.9,
                "confidenceLevel": ConfidenceLevel.HIGH.value,
                "reasoning": "Matched gratitude pattern (fallback)",
                "fromCache": False,
                "processingTimeMs": 0
            }

        # Farewell patterns
        farewell = r"^(bye|goodbye|see\s*you|later|cya|farewell|take\s*care)[\s!.,?]*$"
        if re.match(farewell, lower):
            return {
                "intent": QueryIntent.FAREWELL.value,
                "confidence": 0.9,
                "confidenceLevel": ConfidenceLevel.HIGH.value,
                "reasoning": "Matched farewell pattern (fallback)",
                "fromCache": False,
                "processingTimeMs": 0
            }

        return {
            "intent": QueryIntent.QUESTION.value,
            "confidence": 0.6,
            "confidenceLevel": ConfidenceLevel.LOW.value,
            "reasoning": "Fallback classification - treating as question",
            "fromCache": False,
            "processingTimeMs": 0
        }

    def requires_retrieval(self, intent: QueryIntent) -> bool:
        val = intent.value if isinstance(intent, QueryIntent) else intent
        return val not in [c.value for c in CONVERSATIONAL_INTENTS]

    def get_cache_stats(self) -> dict:
        return self.cache_service.get_stats()

# Singleton service instances
intent_cache_service = IntentCacheService()
conversation_context_service = ConversationContextService()
response_generator_service = ResponseGeneratorService(conversation_context_service)
intent_detection_service = IntentDetectionService(intent_cache_service, conversation_context_service)

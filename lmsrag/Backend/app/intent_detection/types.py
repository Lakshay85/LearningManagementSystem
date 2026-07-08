from enum import Enum
from typing import List, Dict, Any, Optional

class QueryIntent(str, Enum):
    GREETING = 'greeting'
    GRATITUDE = 'gratitude'
    FAREWELL = 'farewell'
    CLARIFICATION = 'clarification'
    FOLLOW_UP = 'follow_up'
    QUESTION = 'question'
    OUT_OF_SCOPE = 'out_of_scope'
    EMPTY = 'empty'
    TOO_LONG = 'too_long'

class ConfidenceLevel(str, Enum):
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'

DEFAULT_INTENT_DETECTION_CONFIG = {
    "confidenceThreshold": 0.7,
    "maxQueryLength": 5000,
    "useEmbeddingFallback": True,
    "llmTemperature": 0.1,
    "maxClassificationTokens": 256,
}

DEFAULT_CACHE_CONFIG = {
    "ttlMs": 300000, # 5 minutes
    "maxSize": 1000,
    "enabled": True,
}

DEFAULT_CONTEXT_CONFIG = {
    "maxHistorySize": 10,
    "sessionTimeoutMs": 3600000, # 1 hour
}

DEFAULT_RESPONSE_CONFIG = {
    "llmTemperature": 0.7,
    "maxResponseTokens": 512,
}

CONVERSATIONAL_INTENTS = [
    QueryIntent.GREETING,
    QueryIntent.GRATITUDE,
    QueryIntent.FAREWELL,
    QueryIntent.OUT_OF_SCOPE,
    QueryIntent.EMPTY,
    QueryIntent.TOO_LONG,
]

RETRIEVAL_INTENTS = [
    QueryIntent.QUESTION,
    QueryIntent.FOLLOW_UP,
    QueryIntent.CLARIFICATION,
]

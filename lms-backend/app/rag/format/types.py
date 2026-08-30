from enum import Enum

class OutputFormat(str, Enum):
    TABLE = 'table'
    LIST = 'list'
    JSON = 'json'
    SUMMARY = 'summary'
    STEPS = 'steps'
    COMPARISON = 'comparison'
    PARAGRAPH = 'paragraph'

class DetectionConfidence(str, Enum):
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'

DEFAULT_FORMAT_CONFIG = {
    "maxRetries": 2,
    "llmTemperature": 0.2,
    "strictMode": False,
    "fallbackToPlainText": True,
    "enableOneShot": True
}

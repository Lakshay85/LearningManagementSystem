import time
from typing import List, Dict, Any, Optional
from groq import AsyncGroq

from app.config import settings
from app.rag.format.types import (
    OutputFormat,
    DEFAULT_FORMAT_CONFIG
)
from app.rag.format.intent_detector import FormatIntent, FormatIntentDetector
from app.rag.format.prompt_templates import PromptTemplateBuilder
from app.rag.format.output_validator import OutputValidator, ValidationResult
from app.rag.format.retrieval_booster import RetrievalBooster, RetrievalBoostResult

class FormatPipelineResult:
    def __init__(
        self,
        content: str,
        format: OutputFormat,
        intent: Any,
        validation: ValidationResult,
        retry_count: int,
        processing_time_ms: int
    ):
        self.content = content
        self.format = format
        self.intent = intent
        self.validation = validation
        self.retryCount = retry_count
        self.processingTimeMs = processing_time_ms

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "format": self.format.value if isinstance(self.format, OutputFormat) else self.format,
            "intent": self.intent.to_dict() if hasattr(self.intent, "to_dict") else self.intent,
            "validation": self.validation.to_dict() if hasattr(self.validation, "to_dict") else self.validation,
            "retryCount": self.retryCount,
            "processingTimeMs": self.processingTimeMs
        }

class FormatPipeline:
    def __init__(self, llm: Optional[Any] = None, config: dict = None):
        cfg = config or {}
        self.config = {
            "maxRetries": cfg.get("maxRetries", DEFAULT_FORMAT_CONFIG["maxRetries"]),
            "llmTemperature": cfg.get("llmTemperature", DEFAULT_FORMAT_CONFIG["llmTemperature"]),
            "strictMode": cfg.get("strictMode", DEFAULT_FORMAT_CONFIG["strictMode"]),
            "fallbackToPlainText": cfg.get("fallbackToPlainText", DEFAULT_FORMAT_CONFIG["fallbackToPlainText"]),
            "enableOneShot": cfg.get("enableOneShot", DEFAULT_FORMAT_CONFIG["enableOneShot"])
        }

        # Initialize Groq client
        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set")
        
        self.llm = AsyncGroq(api_key=self.api_key)
        self.model = settings.GROQ_MODEL or "llama-3.3-70b-versatile"

        self.intent_detector = FormatIntentDetector()
        self.prompt_builder = PromptTemplateBuilder()
        self.validator = OutputValidator()
        self.booster = RetrievalBooster()

    async def execute(self, query: str, context: str) -> FormatPipelineResult:
        start_time = time.time()
        retry_count = 0

        # Step 1: Detect format intent
        print("🎯 Step 1: Detecting format intent...")
        intent = self.intent_detector.detect(query)
        print(f"   Format: {intent.format.value}, Confidence: {intent.confidence.value}")
        print(f"   Signals: {', '.join(intent.signals)}")

        # Step 2: Get retrieval boosts
        boost_result = self.booster.calculate_boosts(intent)
        print(f"🔍 Step 2: Retrieval boosts calculated for {intent.format.value}")

        # Step 3: Build format-specific prompt
        print("📝 Step 3: Building format-specific prompt...")
        prompt = self.prompt_builder.build_prompt(
            intent.format,
            context,
            query,
            self.config["enableOneShot"]
        )

        content = ""
        validation = None

        while True:
            print(f"🤖 Step 4: Generating response (attempt {retry_count + 1})...")
            response_text = await self.generate_with_low_temperature(prompt)
            content = response_text.strip()

            # Step 5: Validate format compliance
            print("✅ Step 5: Validating output format...")
            validation = self.validator.validate(content, intent.format)

            if validation.isValid:
                break

            print(f"⚠️ Validation failed: {', '.join([e.message for e in validation.errors])}")
            
            if retry_count < self.config["maxRetries"]:
                prompt = self.validator.generate_retry_prompt(prompt, intent.format, validation)
                retry_count += 1
                print("🔄 Retrying with stronger format instructions...")
            else:
                if self.config["fallbackToPlainText"]:
                    print("📄 Max retries reached, using response as-is")
                break

        processing_time = int((time.time() - start_time) * 1000)
        print(f"✨ Format pipeline completed in {processing_time}ms")

        return FormatPipelineResult(
            content=content,
            format=intent.format,
            intent=intent,
            validation=validation,
            retry_count=retry_count,
            processing_time_ms=processing_time
        )

    async def generate_with_low_temperature(self, prompt: str) -> str:
        completion = await self.llm.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config["llmTemperature"],
            max_tokens=2048
        )
        return completion.choices[0].message.content or ""

    def get_retrieval_boosts(self, query: str) -> RetrievalBoostResult:
        intent = self.intent_detector.detect(query)
        return self.booster.calculate_boosts(intent)

    def detect_intent(self, query: str) -> FormatIntent:
        return self.intent_detector.detect(query)

    def apply_retrieval_boosts(self, results: List[dict], query: str) -> List[dict]:
        boosts = self.get_retrieval_boosts(query)
        boosted = self.booster.apply_boosts(results, boosts)
        return self.booster.sort_by_boosted_similarity(boosted)

    def validate_output(self, output: str, format: OutputFormat) -> ValidationResult:
        return self.validator.validate(output, format)

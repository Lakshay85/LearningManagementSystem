import json
import httpx
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import AsyncOpenAI
from groq import AsyncGroq
import google.generativeai as genai

from app.config import settings

class TokenUsage:
    def __init__(self, prompt_tokens: int, completion_tokens: int, total_tokens: int):
        self.promptTokens = prompt_tokens
        self.completionTokens = completion_tokens
        self.totalTokens = total_tokens

class LLMResponse:
    def __init__(self, content: str, usage: Optional[TokenUsage] = None, finish_reason: Optional[str] = None):
        self.content = content
        self.usage = usage
        self.finishReason = finish_reason

class StreamChunk:
    def __init__(self, content: str, done: bool, usage: Optional[TokenUsage] = None):
        self.content = content
        self.done = done
        self.usage = usage

# ==================== LLM Providers ====================

class GroqLLMProvider:
    provider = "groq"
    
    def __init__(self, config: dict):
        self.model = config.get("model") or "llama-3.3-70b-versatile"
        self.api_key = config.get("apiKey") or settings.GROQ_API_KEY
        self.client = AsyncGroq(api_key=self.api_key)
        self.temperature = config.get("temperature", 0.4)
        self.max_tokens = config.get("maxTokens", 2048)

    async def generate(self, prompt: str, options: dict = None) -> LLMResponse:
        opts = options or {}
        try:
            chat_completion = await self.client.chat.completions.create(
                model=opts.get("model") or self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=opts.get("temperature", self.temperature),
                max_tokens=opts.get("maxTokens", self.max_tokens)
            )
            choice = chat_completion.choices[0]
            usage = None
            if chat_completion.usage:
                usage = TokenUsage(
                    prompt_tokens=chat_completion.usage.prompt_tokens,
                    completion_tokens=chat_completion.usage.completion_tokens,
                    total_tokens=chat_completion.usage.total_tokens
                )
            return LLMResponse(
                content=choice.message.content or "",
                usage=usage,
                finish_reason=choice.finish_reason
            )
        except Exception as e:
            print(f"Groq generation error: {str(e)}")
            raise Exception(f"Groq generation failed: {str(e)}")

    async def generate_stream(self, prompt: str, options: dict = None) -> AsyncGenerator[StreamChunk, None]:
        opts = options or {}
        try:
            stream = await self.client.chat.completions.create(
                model=opts.get("model") or self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=opts.get("temperature", self.temperature),
                max_tokens=opts.get("maxTokens", self.max_tokens),
                stream=True
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                done = chunk.choices[0].finish_reason is not None
                yield StreamChunk(content=delta, done=done)
        except Exception as e:
            print(f"Groq streaming error: {str(e)}")
            raise Exception(f"Groq streaming failed: {str(e)}")

    async def is_available(self) -> bool:
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False

    def estimate_tokens(self, text: str) -> int:
        return -(-len(text) // 4)  # Math.ceil(len(text)/4)


class OpenAILLMProvider:
    provider = "openai"

    def __init__(self, config: dict):
        self.model = config.get("model") or "gpt-4o-mini"
        self.api_key = config.get("apiKey") or settings.OPENAI_API_KEY
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.temperature = config.get("temperature", 0.4)
        self.max_tokens = config.get("maxTokens", 2048)

    async def generate(self, prompt: str, options: dict = None) -> LLMResponse:
        opts = options or {}
        try:
            chat_completion = await self.client.chat.completions.create(
                model=opts.get("model") or self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=opts.get("temperature", self.temperature),
                max_tokens=opts.get("maxTokens", self.max_tokens)
            )
            choice = chat_completion.choices[0]
            usage = None
            if chat_completion.usage:
                usage = TokenUsage(
                    prompt_tokens=chat_completion.usage.prompt_tokens,
                    completion_tokens=chat_completion.usage.completion_tokens,
                    total_tokens=chat_completion.usage.total_tokens
                )
            return LLMResponse(
                content=choice.message.content or "",
                usage=usage,
                finish_reason=choice.finish_reason
            )
        except Exception as e:
            print(f"OpenAI generation error: {str(e)}")
            raise Exception(f"OpenAI generation failed: {str(e)}")

    async def generate_stream(self, prompt: str, options: dict = None) -> AsyncGenerator[StreamChunk, None]:
        opts = options or {}
        try:
            stream = await self.client.chat.completions.create(
                model=opts.get("model") or self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=opts.get("temperature", self.temperature),
                max_tokens=opts.get("maxTokens", self.max_tokens),
                stream=True
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                done = chunk.choices[0].finish_reason is not None
                yield StreamChunk(content=delta, done=done)
        except Exception as e:
            print(f"OpenAI streaming error: {str(e)}")
            raise Exception(f"OpenAI streaming failed: {str(e)}")

    async def is_available(self) -> bool:
        try:
            await self.client.models.retrieve(self.model)
            return True
        except Exception:
            return False

    def estimate_tokens(self, text: str) -> int:
        return -(-len(text) // 4)

# ==================== Embedding Providers ====================

class OpenAIEmbeddingProvider:
    provider = "openai"

    def __init__(self, config: dict):
        self.model = config.get("model") or "text-embedding-3-small"
        self.dimensions = config.get("dimensions") or 1536
        self.api_key = config.get("apiKey") or settings.OPENAI_API_KEY
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def embed(self, text: str) -> dict:
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions
            )
            return {
                "embedding": response.data[0].embedding,
                "usage": {"totalTokens": response.usage.total_tokens} if response.usage else None
            }
        except Exception as e:
            print(f"OpenAI embedding error: {str(e)}")
            raise Exception(f"OpenAI embedding failed: {str(e)}")

    async def embed_batch(self, texts: List[str]) -> dict:
        try:
            batch_size = 100
            all_embeddings = []
            total_tokens = 0
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    dimensions=self.dimensions
                )
                all_embeddings.extend([d.embedding for d in response.data])
                if response.usage:
                    total_tokens += response.usage.total_tokens
                    
            return {
                "embeddings": all_embeddings,
                "usage": {"totalTokens": total_tokens}
            }
        except Exception as e:
            print(f"OpenAI batch embedding error: {str(e)}")
            raise Exception(f"OpenAI batch embedding failed: {str(e)}")

    async def is_available(self) -> bool:
        try:
            await self.embed("test")
            return True
        except Exception:
            return False


class GeminiEmbeddingProvider:
    provider = "gemini"

    def __init__(self, config: dict):
        self.model = config.get("model") or "models/gemini-embedding-001"
        self.dimensions = 3072
        self.api_key = config.get("apiKey") or settings.GEMINI_API_KEY
        genai.configure(api_key=self.api_key)

    async def embed(self, text: str) -> dict:
        try:
            # We run in executor because google-generativeai call is synchronous
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: genai.embed_content(
                    model=self.model,
                    content=text,
                    task_type="retrieval_document"
                )
            )
            return {
                "embedding": response["embedding"]
            }
        except Exception as e:
            print(f"Gemini embedding error: {str(e)}")
            raise Exception(f"Gemini embedding failed: {str(e)}")

    async def embed_batch(self, texts: List[str]) -> dict:
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: genai.embed_content(
                    model=self.model,
                    content=texts,
                    task_type="retrieval_document"
                )
            )
            return {
                "embeddings": response["embedding"]
            }
        except Exception as e:
            print(f"Gemini batch embedding error: {str(e)}")
            raise Exception(f"Gemini batch embedding failed: {str(e)}")

    async def is_available(self) -> bool:
        try:
            await self.embed("test")
            return True
        except Exception:
            return False


class NvidiaEmbeddingProvider:
    provider = "nvidia"

    def __init__(self, config: dict):
        self.model = config.get("model") or "baai/bge-m3"
        self.dimensions = 1024
        self.api_key = config.get("apiKey") or settings.NVIDIA_API_KEY
        self.base_url = config.get("baseUrl") or "https://integrate.api.nvidia.com/v1"
        print("🟢 NVIDIA Embedding Provider initialized")

    async def embed(self, text: str) -> dict:
        return await self.embed_with_type(text, "query")

    async def embed_with_type(self, text: str, input_type: str) -> dict:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "input": [text],
                "model": self.model,
                "encoding_format": "float",
                "input_type": input_type
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(f"{self.base_url}/embeddings", json=payload, headers=headers)
                if res.status_code != 200:
                    raise Exception(f"NVIDIA API error: {res.status_code} - {res.text}")
                
                data = res.json()
                embedding = data["data"][0]["embedding"]
                total_tokens = data.get("usage", {}).get("total_tokens")
                return {
                    "embedding": embedding,
                    "usage": {"totalTokens": total_tokens} if total_tokens else None
                }
        except Exception as e:
            print(f"NVIDIA embedding error: {str(e)}")
            raise Exception(f"NVIDIA embedding failed: {str(e)}")

    async def embed_batch(self, texts: List[str]) -> dict:
        try:
            batch_size = 50
            all_embeddings = []
            total_tokens = 0
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                payload = {
                    "input": batch,
                    "model": self.model,
                    "encoding_format": "float",
                    "input_type": "passage"
                }
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    res = await client.post(f"{self.base_url}/embeddings", json=payload, headers=headers)
                    if res.status_code != 200:
                        raise Exception(f"NVIDIA API error: {res.status_code} - {res.text}")
                    
                    data = res.json()
                    # Sort data by index
                    sorted_data = sorted(data["data"], key=lambda item: item["index"])
                    all_embeddings.extend([item["embedding"] for item in sorted_data])
                    
                    total_tokens += data.get("usage", {}).get("total_tokens", 0)

            return {
                "embeddings": all_embeddings,
                "usage": {"totalTokens": total_tokens}
            }
        except Exception as e:
            print(f"NVIDIA batch embedding error: {str(e)}")
            raise Exception(f"NVIDIA batch embedding failed: {str(e)}")

    async def is_available(self) -> bool:
        try:
            await self.embed("test")
            return True
        except Exception:
            return False

# ==================== Factory Helpers ====================

def create_llm_provider(config: dict):
    provider = config.get("provider")
    if provider == "openai":
        return OpenAILLMProvider(config)
    elif provider == "groq":
        return GroqLLMProvider(config)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")

def create_embedding_provider(config: dict):
    provider = config.get("provider")
    if provider == "openai":
        return OpenAIEmbeddingProvider(config)
    elif provider == "gemini":
        return GeminiEmbeddingProvider(config)
    elif provider == "nvidia":
        return NvidiaEmbeddingProvider(config)
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")

# ==================== Provider Managers ====================

class LLMProviderManager:
    def __init__(self, primary_config: dict, fallback_config: dict = None):
        self.primary = create_llm_provider(primary_config)
        self.fallback = create_llm_provider(fallback_config) if fallback_config else None
        self.use_fallback = False
        self.consecutive_failures = 0
        self.max_failures = 3
        print(f"🤖 Primary LLM: {primary_config.get('provider')}/{primary_config.get('model')}")

    @property
    def current_provider(self):
        return self.fallback if (self.use_fallback and self.fallback) else self.primary

    async def generate(self, prompt: str, options: dict = None) -> LLMResponse:
        try:
            res = await self.current_provider.generate(prompt, options)
            self.consecutive_failures = 0
            return res
        except Exception as e:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.max_failures and self.fallback:
                print("🔄 Switching to fallback LLM provider")
                self.use_fallback = True
                self.consecutive_failures = 0
                return await self.fallback.generate(prompt, options)
            raise e

    async def generate_stream(self, prompt: str, options: dict = None) -> AsyncGenerator[StreamChunk, None]:
        try:
            async for chunk in self.current_provider.generate_stream(prompt, options):
                yield chunk
            self.consecutive_failures = 0
        except Exception as e:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.max_failures and self.fallback:
                print("🔄 Switching to fallback LLM provider for stream")
                self.use_fallback = True
                self.consecutive_failures = 0
                async for chunk in self.fallback.generate_stream(prompt, options):
                    yield chunk
            else:
                raise e


class EmbeddingProviderManager:
    def __init__(self, primary_config: dict, fallback_config: dict = None):
        self.primary = create_embedding_provider(primary_config)
        self.fallback = create_embedding_provider(fallback_config) if fallback_config else None
        self.use_fallback = False
        self.consecutive_failures = 0
        self.max_failures = 3
        print(f"📊 Primary embeddings: {primary_config.get('provider')}/{primary_config.get('model')}")

    @property
    def current_provider(self):
        return self.fallback if (self.use_fallback and self.fallback) else self.primary

    @property
    def dimensions(self) -> int:
        return self.current_provider.dimensions

    async def embed(self, text: str) -> dict:
        try:
            res = await self.current_provider.embed(text)
            self.consecutive_failures = 0
            return res
        except Exception as e:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.max_failures and self.fallback:
                print("🔄 Switching to fallback embedding provider")
                self.use_fallback = True
                self.consecutive_failures = 0
                return await self.fallback.embed(text)
            raise e

    async def embed_batch(self, texts: List[str]) -> dict:
        try:
            res = await self.current_provider.embed_batch(texts)
            self.consecutive_failures = 0
            return res
        except Exception as e:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.max_failures and self.fallback:
                print("🔄 Switching to fallback embedding provider for batch")
                self.use_fallback = True
                self.consecutive_failures = 0
                return await self.fallback.embed_batch(texts)
            raise e

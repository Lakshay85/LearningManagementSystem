import os
from typing import List, Dict, Any
from langchain_core.documents import Document

from app.config import settings
from app.llm.providers import (
    OpenAIEmbeddingProvider,
    GeminiEmbeddingProvider,
    NvidiaEmbeddingProvider
)

class EmbeddingResult:
    def __init__(self, embeddings: List[List[float]], documents: List[Document]):
        self.embeddings = embeddings
        self.documents = documents

class Embedder:
    def __init__(self, config: dict):
        self.provider = config.get("provider") or os.getenv("EMBEDDING_PROVIDER", "nvidia")
        api_key = config.get("apiKey")
        model_name = config.get("modelName")
        dimensions = config.get("dimensions")

        if self.provider == "gemini":
            self.provider_instance = GeminiEmbeddingProvider({
                "apiKey": api_key or settings.GEMINI_API_KEY,
                "model": model_name or os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
            })
        elif self.provider == "openai":
            self.provider_instance = OpenAIEmbeddingProvider({
                "apiKey": api_key or settings.OPENAI_API_KEY,
                "model": model_name or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
                "dimensions": dimensions or int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
            })
        elif self.provider == "nvidia":
            self.provider_instance = NvidiaEmbeddingProvider({
                "apiKey": api_key or settings.NVIDIA_API_KEY,
                "model": model_name or os.getenv("EMBEDDING_MODEL", "baai/bge-m3")
            })
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

    async def embed_documents(self, documents: List[Document]) -> EmbeddingResult:
        try:
            texts = [doc.page_content for doc in documents]
            
            res = await self.provider_instance.embed_batch(texts)
            embeddings = res["embeddings"]

            # Attach embeddings to documents metadata (to match JS behavior)
            enriched_documents = []
            for index, doc in enumerate(documents):
                doc.metadata["embedding"] = embeddings[index]
                enriched_documents.append(doc)

            return EmbeddingResult(
                embeddings=embeddings,
                documents=enriched_documents
            )
        except Exception as e:
            raise Exception(f"Failed to embed documents: {str(e)}")

    async def embed_query(self, text: str) -> List[float]:
        try:
            if self.provider == "nvidia":
                res = await self.provider_instance.embed_with_type(text, "query")
            else:
                res = await self.provider_instance.embed(text)
            return res["embedding"]
        except Exception as e:
            raise Exception(f"Failed to embed query: {str(e)}")

    @classmethod
    def create_google_embedder(cls, api_key: str = None, model_name: str = None) -> 'Embedder':
        return cls({
            "provider": "gemini",
            "apiKey": api_key,
            "modelName": model_name
        })

    @classmethod
    def create_openai_embedder(cls, api_key: str = None, model_name: str = None) -> 'Embedder':
        return cls({
            "provider": "openai",
            "apiKey": api_key,
            "modelName": model_name
        })

    @classmethod
    def create_nvidia_embedder(cls, api_key: str = None, model_name: str = None) -> 'Embedder':
        return cls({
            "provider": "nvidia",
            "apiKey": api_key,
            "modelName": model_name or "baai/bge-m3"
        })

    @classmethod
    def create_from_env(cls) -> 'Embedder':
        provider = os.getenv("EMBEDDING_PROVIDER") or "nvidia"
        print(f"🔧 Creating embedder with provider: {provider}")
        print(f"   EMBEDDING_PROVIDER env: {os.getenv('EMBEDDING_PROVIDER')}")
        print(f"   NVIDIA_API_KEY set: {bool(os.getenv('NVIDIA_API_KEY'))}")
        print(f"   EMBEDDING_MODEL: {os.getenv('EMBEDDING_MODEL', 'default')}")

        if provider == "nvidia":
            print("📊 Using NVIDIA bge-m3 embeddings (1024 dimensions)")
            return cls.create_nvidia_embedder()
        elif provider == "openai":
            print("📊 Using OpenAI embeddings")
            return cls.create_openai_embedder()
        elif provider == "gemini":
            print("📊 Using Gemini embeddings (3072 dimensions)")
            return cls.create_google_embedder()
        else:
            print("📊 Defaulting to NVIDIA embeddings")
            return cls.create_nvidia_embedder()

    def get_provider(self) -> str:
        return self.provider

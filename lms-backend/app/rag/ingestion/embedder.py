import os
from typing import List, Dict, Any
from langchain_core.documents import Document

from app.config import settings
from app.llm.providers import (
    OpenAIEmbeddingProvider,
    GeminiEmbeddingProvider,
    NvidiaEmbeddingProvider,
    FastEmbedEmbeddingProvider
)

class EmbeddingResult:
    def __init__(self, embeddings: List[List[float]], documents: List[Document]):
        self.embeddings = embeddings
        self.documents = documents

class Embedder:
    def __init__(self, config: dict = None):
        cfg = config or {}
        self.provider = cfg.get("provider") or getattr(settings, "EMBEDDING_PROVIDER", None) or os.getenv("EMBEDDING_PROVIDER", "fastembed")
        api_key = cfg.get("apiKey")
        model_name = cfg.get("modelName") or getattr(settings, "EMBEDDING_MODEL", None)
        dimensions = cfg.get("dimensions") or getattr(settings, "EMBEDDING_DIMENSIONS", 1024)

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
        elif self.provider in ["fastembed", "local"]:
            self.provider_instance = FastEmbedEmbeddingProvider({
                "model": model_name or "BAAI/bge-large-en-v1.5"
            })
        else:
            self.provider_instance = FastEmbedEmbeddingProvider({
                "model": model_name or "BAAI/bge-large-en-v1.5"
            })

    async def embed_documents(self, documents: List[Document]) -> EmbeddingResult:
        try:
            texts = [doc.page_content for doc in documents]
            res = await self.provider_instance.embed_batch(texts)
            embeddings = res["embeddings"]

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

    async def embed_query(self, query: str) -> List[float]:
        try:
            res = await self.provider_instance.embed(query)
            return res["embedding"]
        except Exception as e:
            raise Exception(f"Failed to embed query: {str(e)}")

    async def is_ready(self) -> bool:
        return await self.provider_instance.is_available()

    @classmethod
    def create_from_env(cls):
        provider = getattr(settings, "EMBEDDING_PROVIDER", None) or os.getenv("EMBEDDING_PROVIDER", "fastembed")
        model = getattr(settings, "EMBEDDING_MODEL", None) or os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
        return cls({
            "provider": provider,
            "modelName": model
        })

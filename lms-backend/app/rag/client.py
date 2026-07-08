import httpx
import json
from typing import Dict, Any, Optional

from app.config import settings

class RagClient:
    def __init__(self):
        self.api_url = settings.RAG_API_URL
        self.api_key = settings.RAG_API_KEY

    async def ingest_document(
        self,
        file_buffer: bytes,
        file_name: str,
        mime_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        endpoint = "/v1/rag/ingest/document"
        if mime_type == "application/pdf":
            endpoint = "/v1/rag/ingest/pdf"

        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        files = {
            "file": (file_name, file_buffer, mime_type)
        }
        data = {}
        if metadata:
            data["metadata"] = json.dumps(metadata)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.api_url}{endpoint}",
                files=files,
                data=data,
                headers=headers
            )
            
            if response.status_code not in (200, 201):
                raise Exception(f"RAG API error: {response.status_code} - {response.text}")

            result = response.json()
            data_res = result.get("data", {})
            return {
                "docId": data_res.get("docId", ""),
                "chunks": data_res.get("chunks", 0)
            }

    async def ingest_video_transcript(
        self,
        transcript: str,
        video_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key

        payload = {
            "transcript": transcript,
            "videoName": video_name,
            "metadata": metadata or {}
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.api_url}/v1/rag/ingest/video",
                json=payload,
                headers=headers
            )
            
            if response.status_code not in (200, 201):
                raise Exception(f"RAG API error: {response.status_code} - {response.text}")

            result = response.json()
            data_res = result.get("data", {})
            return {
                "docId": data_res.get("docId", ""),
                "chunks": data_res.get("chunks", 0)
            }

rag_client = RagClient()

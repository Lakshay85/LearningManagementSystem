import json
import uuid
import time
import os
from typing import List, Dict, Any, Optional, Callable
import redis.asyncio as aioredis
from arq import create_pool
from arq.connections import RedisSettings

from app.config import settings

class IngestionStatus:
    QUEUED = 'queued'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    RETRYING = 'retrying'

class IngestionStage:
    QUEUED = 'queued'
    UPLOADING = 'uploading'
    PARSING = 'parsing'
    CHUNKING = 'chunking'
    EMBEDDING = 'embedding'
    STORING = 'storing'
    COMPLETE = 'complete'
    FAILED = 'failed'

STAGE_PROGRESS = {
    IngestionStage.QUEUED: 0,
    IngestionStage.UPLOADING: 10,
    IngestionStage.PARSING: 25,
    IngestionStage.CHUNKING: 45,
    IngestionStage.EMBEDDING: 65,
    IngestionStage.STORING: 85,
    IngestionStage.COMPLETE: 100,
    IngestionStage.FAILED: -1,
}

class IngestionQueueService:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.arq_pool = None
        self.is_enabled = False
        self.processor: Optional[Callable] = None
        self.queue_name = 'arq:queue'

    async def connect(self):
        redis_url = settings.REDIS_URL
        if not redis_url:
            print("⚠️ REDIS_URL not configured, async ingestion disabled")
            return

        try:
            self.redis = aioredis.from_url(redis_url, decode_responses=True)
            await self.redis.ping()
            
            # Setup arq pool
            redis_settings = RedisSettings.from_dsn(redis_url)
            self.arq_pool = await create_pool(redis_settings)
            
            self.is_enabled = True
            print("✅ Ingestion Queue initialized (arq pool)")
        except Exception as e:
            print(f"Failed to initialize ingestion queue: {str(e)}")

    async def disconnect(self):
        if self.arq_pool:
            await self.arq_pool.close()
        if self.redis:
            await self.redis.close()

    def register_processor(self, processor: Callable):
        self.processor = processor
        print("📦 Ingestion worker processor registered")

    async def add_to_queue(self, data: dict) -> str:
        if not self.is_enabled or not self.arq_pool:
            raise Exception("Async ingestion not available. Process synchronously instead.")

        task_id = str(uuid.uuid4())
        
        # Initialize progress tracking
        progress = {
            "taskId": task_id,
            "status": IngestionStatus.QUEUED,
            "stage": IngestionStage.QUEUED,
            "progress": 0,
            "message": "Document queued for processing",
            "createdAt": time.time(),
            "updatedAt": time.time()
        }
        await self.update_progress(task_id, progress)

        # Enqueue job to arq
        # Job payload will contain task_id
        await self.arq_pool.enqueue_job("ingest_document_job", {**data, "taskId": task_id})
        
        print(f"📥 Added ingestion job: {task_id} ({data.get('fileName')})")
        return task_id

    async def get_status(self, task_id: str) -> Optional[dict]:
        if not self.redis:
            return None

        val = await self.redis.get(f"ingestion:{task_id}")
        if not val:
            return None
        return json.loads(val)

    def is_queue_enabled(self) -> bool:
        return self.is_enabled

    async def update_progress(self, task_id: str, progress_data: dict) -> None:
        if not self.redis:
            return

        existing = await self.get_status(task_id) or {}
        updated = {
            **existing,
            **progress_data,
            "taskId": task_id,
            "updatedAt": time.time()
        }
        if "createdAt" not in updated:
            updated["createdAt"] = time.time()

        # TTL = 24 hours
        await self.redis.setex(f"ingestion:{task_id}", 86400, json.dumps(updated))

    async def get_queue_stats(self) -> dict:
        if not self.redis:
            return {"waiting": 0, "active": 0, "completed": 0, "failed": 0}
        # In arq/redis, we can query length of queue keys or similar
        # For simplicity, return mock/approximated stats
        return {
            "waiting": await self.redis.llen(self.queue_name) if await self.redis.exists(self.queue_name) else 0,
            "active": 0,
            "completed": 0,
            "failed": 0
        }

# Global singleton service
ingestion_queue_service = IngestionQueueService()

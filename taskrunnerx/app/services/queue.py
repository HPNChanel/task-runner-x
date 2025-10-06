
import json

from redis import asyncio as aioredis

from ..config import get_settings

settings = get_settings()


class Queue:
    def __init__(self):
        self._redis: aioredis.Redis | None = None
        self.stream = settings.redis_stream
    
    async def connect(self):
        if not self._redis:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    
    async def close(self):
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    async def enqueue(self, task_id: int, name: str, payload: dict |None = None):
        await self.connect()
        data = {
            "task_id": str(task_id),
            "name": name,
            "payload": json.dumps(payload or {}),
        }
        
        #* XADD for Redis Streams
        msg_id = await self._redis.xadd(self.stream, fields=data, maxlen=10000, approximate=True)
        return msg_id


queue = Queue()

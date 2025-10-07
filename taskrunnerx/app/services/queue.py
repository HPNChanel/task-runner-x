import json
from typing import Any, cast

from redis import asyncio as aioredis

from ..config import get_settings

settings = get_settings()


class Queue:
    def __init__(self) -> None:
        self._redis: aioredis.Redis | None = None
        self.stream = settings.redis_stream

    async def connect(self) -> None:
        if not self._redis:
            redis_factory: Any = aioredis.from_url
            self._redis = cast(
                aioredis.Redis,
                redis_factory(settings.redis_url, decode_responses=True),
            )

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def enqueue(
        self,
        task_id: int,
        name: str,
        payload: dict[str, Any] | None = None,
    ) -> str:
        await self.connect()
        data: dict[str, str] = {
            "task_id": str(task_id),
            "name": name,
            "payload": json.dumps(payload or {}),
        }

        redis = self._redis
        if redis is None:
            msg = "Redis connection not established"
            raise RuntimeError(msg)

        # * XADD for Redis Streams
        fields = cast(dict[Any, Any], data)
        result = await redis.xadd(
            self.stream,
            fields=fields,
            maxlen=10000,
            approximate=True,
        )
        return cast(str, result)


queue = Queue()

"""Idempotency adapter using Redis."""

from typing import Optional
import redis

from ..config import config
from ..domain.errors import IdempotencyViolation
from ..logging import get_logger

logger = get_logger(__name__)


class IdempotencyAdapter:
    """Redis-based idempotency lock."""
    
    def __init__(self, redis_url: str = config.REDIS_URL):
        self.redis = redis.from_url(redis_url)
        
    def acquire_lock(
        self,
        idempotency_key: str,
        value: str,
        ttl: int = 3600
    ) -> bool:
        """Acquire idempotency lock."""
        result = self.redis.set(
            f"idempotency:{idempotency_key}",
            value,
            nx=True,
            ex=ttl
        )
        
        if result:
            logger.info(f"Acquired idempotency lock: {idempotency_key}")
            return True
        else:
            logger.warning(f"Idempotency lock already exists: {idempotency_key}")
            raise IdempotencyViolation(f"Operation with key {idempotency_key} already in progress")
            
    def release_lock(self, idempotency_key: str) -> None:
        """Release idempotency lock."""
        self.redis.delete(f"idempotency:{idempotency_key}")
        logger.info(f"Released idempotency lock: {idempotency_key}")
        
    def get_lock_value(self, idempotency_key: str) -> Optional[str]:
        """Get current lock value."""
        value = self.redis.get(f"idempotency:{idempotency_key}")
        return value.decode() if value else None

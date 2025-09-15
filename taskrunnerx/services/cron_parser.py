"""Cron expression parser."""

from datetime import datetime, timedelta
from typing import Optional

from ..logging import get_logger

logger = get_logger(__name__)


class CronParser:
    """Simple cron expression parser."""
    
    def get_next_run(self, cron_expr: str, from_time: Optional[datetime] = None) -> datetime:
        """Get next run time for cron expression."""
        if from_time is None:
            from_time = datetime.utcnow()
            
        # This is a simplified implementation
        # In production, use croniter or similar library
        
        parts = cron_expr.split()
        if len(parts) != 5:
            raise ValueError("Invalid cron expression format")
            
        minute, hour, day, month, weekday = parts
        
        # Handle simple cases
        if cron_expr == "0 * * * *":  # Every hour
            next_run = from_time.replace(minute=0, second=0, microsecond=0)
            if next_run <= from_time:
                next_run += timedelta(hours=1)
            return next_run
            
        elif cron_expr == "*/5 * * * *":  # Every 5 minutes
            current_minute = from_time.minute
            next_minute = ((current_minute // 5) + 1) * 5
            
            if next_minute >= 60:
                next_run = from_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            else:
                next_run = from_time.replace(minute=next_minute, second=0, microsecond=0)
                
            return next_run
            
        # Default to next hour for unsupported expressions
        logger.warning(f"Unsupported cron expression: {cron_expr}, defaulting to hourly")
        next_run = from_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        return next_run

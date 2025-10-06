"""Metrics collection."""

from collections import defaultdict
from typing import Any, Dict


class Metrics:
    """Simple in-memory metrics collector."""
    
    def __init__(self):
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, list] = defaultdict(list)
        
    def increment(self, metric: str, value: int = 1) -> None:
        """Increment counter metric."""
        self.counters[metric] += value
        
    def timer(self, metric: str, duration: float) -> None:
        """Record timer metric."""
        self.timers[metric].append(duration)
        
    def get_stats(self) -> Dict[str, Any]:
        """Get all metrics."""
        return {
            "counters": dict(self.counters),
            "timers": {
                k: {
                    "count": len(v),
                    "avg": sum(v) / len(v) if v else 0,
                    "total": sum(v)
                }
                for k, v in self.timers.items()
            }
        }


metrics = Metrics()

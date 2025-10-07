"""Metrics collection."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Metrics:
    """Simple in-memory metrics collector."""

    counters: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))
    timers: defaultdict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    def increment(self, metric: str, value: int = 1) -> None:
        """Increment counter metric."""
        self.counters[metric] += value

    def timer(self, metric: str, duration: float) -> None:
        """Record timer metric."""
        self.timers[metric].append(duration)

    def get_stats(self) -> dict[str, Any]:
        """Get all metrics."""
        return {
            "counters": dict(self.counters),
            "timers": {
                key: {
                    "count": len(values),
                    "avg": sum(values) / len(values) if values else 0.0,
                    "total": sum(values),
                }
                for key, values in self.timers.items()
            },
        }


metrics = Metrics()

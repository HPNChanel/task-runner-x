"""Worker-side metrics helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from types import TracebackType


@dataclass(slots=True)
class Timer:
    """Simple context manager to record elapsed wall-clock time."""

    start: float = field(init=False, default=0.0)
    elapsed: float = field(init=False, default=0.0)

    def __enter__(self) -> Timer:
        self.start = time()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        _ = exc_type, exc, tb  # Unused hook parameters.
        self.elapsed = time() - self.start

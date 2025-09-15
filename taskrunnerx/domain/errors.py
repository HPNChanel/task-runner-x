"""Domain exceptions."""


class TaskRunnerError(Exception):
    """Base exception for TaskRunner."""
    pass


class JobNotFound(TaskRunnerError):
    """Job not found exception."""
    pass


class ScheduleNotFound(TaskRunnerError):
    """Schedule not found exception."""
    pass


class TaskNotFound(TaskRunnerError):
    """Task function not found."""
    pass


class TaskExecutionError(TaskRunnerError):
    """Task execution failed."""
    pass


class IdempotencyViolation(TaskRunnerError):
    """Idempotency key already exists."""
    pass

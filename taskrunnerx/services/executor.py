"""Task executor for running task functions."""

import importlib
import signal
from typing import Any, Dict, Callable

from ..domain.models import ExecutionResult
from ..domain.errors import TaskNotFound, TaskExecutionError
from ..logging import get_logger

logger = get_logger(__name__)


class TimeoutError(Exception):
    """Task execution timeout."""
    pass


class TaskExecutor:
    """Execute task functions dynamically."""
    
    def __init__(self):
        self._task_registry: Dict[str, Callable] = {}
        self._load_builtin_tasks()
        
    def register_task(self, name: str, func: Callable) -> None:
        """Register task function."""
        self._task_registry[name] = func
        logger.info(f"Registered task: {name}")
        
    def execute(
        self,
        task_name: str,
        args: Dict[str, Any],
        kwargs: Dict[str, Any],
        timeout: int = 300
    ) -> ExecutionResult:
        """Execute task with timeout."""
        if task_name not in self._task_registry:
            # Try to import task dynamically
            try:
                self._import_task(task_name)
            except Exception as e:
                return ExecutionResult(
                    success=False,
                    error=f"Task not found: {task_name} ({e})",
                    duration=0.0
                )
                
        task_func = self._task_registry[task_name]
        
        # Set up timeout handler
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Task {task_name} timed out after {timeout}s")
            
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            import time
            start_time = time.time()
            
            # Execute task
            result = task_func(*args.values() if args else [], **kwargs)
            
            duration = time.time() - start_time
            
            return ExecutionResult(
                success=True,
                result=result,
                duration=duration
            )
            
        except TimeoutError as e:
            return ExecutionResult(
                success=False,
                error=str(e),
                duration=timeout
            )
        except Exception as e:
            import time
            duration = time.time() - start_time if 'start_time' in locals() else 0.0
            return ExecutionResult(
                success=False,
                error=str(e),
                duration=duration
            )
        finally:
            signal.alarm(0)  # Cancel timeout
            signal.signal(signal.SIGALRM, old_handler)  # Restore handler
            
    def _import_task(self, task_name: str) -> None:
        """Import task function dynamically."""
        parts = task_name.split(".")
        if len(parts) < 2:
            raise TaskNotFound(f"Invalid task name format: {task_name}")
            
        module_path = ".".join(parts[:-1])
        func_name = parts[-1]
        
        try:
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            self.register_task(task_name, func)
        except (ImportError, AttributeError) as e:
            raise TaskNotFound(f"Could not import {task_name}: {e}")
            
    def _load_builtin_tasks(self) -> None:
        """Load built-in tasks."""
        try:
            from ..tasks.builtin import echo, sleep, http_call, shell
            
            self.register_task("echo", echo)
            self.register_task("sleep", sleep)
            self.register_task("http_call", http_call)
            self.register_task("shell", shell)
            
        except ImportError:
            logger.warning("Could not load built-in tasks")

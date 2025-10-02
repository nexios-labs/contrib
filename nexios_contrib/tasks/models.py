"""
Data models for the task management system.

This module defines the core data structures used by the task system.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Union
from uuid import UUID, uuid4

from .config import TaskStatus

T = TypeVar('T')

@dataclass
class TaskResult:
    """Represents the result of a completed task."""
    task_id: str
    result: Any
    status: TaskStatus
    error: Optional[Exception] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the task result to a dictionary."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": str(self.result) if self.result is not None else None,
            "error": str(self.error) if self.error else None,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "duration": (self.completed_at or time.time()) - self.created_at
        }

@dataclass
class TaskError:
    """Represents an error that occurred during task execution."""
    message: str
    exception_type: str
    traceback: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary."""
        return {
            "message": self.message,
            "exception_type": self.exception_type,
            "traceback": self.traceback
        }

class Task:
    """Represents a background task.
    
    This class encapsulates a coroutine that runs in the background and provides
    methods to monitor and control its execution.
    """
    
    def __init__(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        name: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """Initialize a new task.
        
        Args:
            func: The coroutine function to execute.
            *args: Positional arguments to pass to the function.
            name: Optional name for the task.
            **kwargs: Keyword arguments to pass to the function.
        """
        self.id = str(uuid4())
        self.name = name or f"task-{self.id[:8]}"
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._task: Optional[asyncio.Task] = None
        self._result: Optional[TaskResult] = None
        self._status: TaskStatus = TaskStatus.PENDING
        self._created_at = time.time()
        self._started_at: Optional[float] = None
        self._completed_at: Optional[float] = None
        self._done_event = asyncio.Event()
    
    @property
    def status(self) -> TaskStatus:
        """Get the current status of the task."""
        return self._status
    
    @property
    def result(self) -> Optional[TaskResult]:
        """Get the result of the task if it has completed."""
        return self._result
    
    @property
    def is_done(self) -> bool:
        """Check if the task has completed (successfully or not)."""
        return self._status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
    
    async def run(self) -> None:
        """Execute the task."""
        if self._status != TaskStatus.PENDING:
            raise RuntimeError(f"Task {self.id} has already been executed")
        
        self._status = TaskStatus.RUNNING
        self._started_at = time.time()
        
        try:
            result = await self.func(*self.args, **self.kwargs)
            self._result = TaskResult(
                task_id=self.id,
                result=result,
                status=TaskStatus.COMPLETED,
                completed_at=time.time()
            )
            self._status = TaskStatus.COMPLETED
        except asyncio.CancelledError:
            self._status = TaskStatus.CANCELLED
            self._result = TaskResult(
                task_id=self.id,
                result=None,
                status=TaskStatus.CANCELLED,
                completed_at=time.time()
            )
            raise
        except Exception as e:
            import traceback
            self._status = TaskStatus.FAILED
            self._result = TaskResult(
                task_id=self.id,
                result=None,
                status=TaskStatus.FAILED,
                error=e,
                completed_at=time.time()
            )
            raise
        finally:
            self._completed_at = time.time()
            self._done_event.set()
    
    async def wait(self, timeout: Optional[float] = None) -> Any:
        """Wait for the task to complete and return its result.
        
        Args:
            timeout: Optional timeout in seconds.
            
        Returns:
            The result of the task.
            
        Raises:
            asyncio.TimeoutError: If the task times out.
            Exception: If the task raises an exception.
        """
        if self._result is not None:
            if self._status == TaskStatus.FAILED and self._result.error:
                raise self._result.error
            return self._result.result
            
        try:
            await asyncio.wait_for(self._done_event.wait(), timeout=timeout)
            if self._result and self._status == TaskStatus.FAILED and self._result.error:
                raise self._result.error
            return self._result.result if self._result else None
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f"Task {self.id} timed out after {timeout} seconds")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the task to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "status": self._status.value,
            "created_at": self._created_at,
            "started_at": self._started_at,
            "completed_at": self._completed_at,
            "duration": (self._completed_at or time.time()) - (self._started_at or self._created_at) if self._started_at else None,
            "result": self._result.to_dict() if self._result else None
        }

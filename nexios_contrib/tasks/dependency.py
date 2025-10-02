"""
Dependency injection for Nexios tasks.

This module provides dependency injection utilities for working with background tasks.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar, Union, Generic, Type
from uuid import UUID, uuid4
import asyncio
import logging

from nexios.dependencies import Depend,Context
from nexios.http import Request

from .config import TaskStatus, TaskConfig
from .models import Task, TaskResult, TaskError

T = TypeVar('T')
TaskCallback = Callable[..., Awaitable[Any]]
TaskResultCallback = Callable[[str, Any, Optional[Exception]], Awaitable[None]]

class TaskDepend(Generic[T]):
    """Dependency for working with background tasks.
    
    This class provides methods for creating and managing background tasks.
    It's designed to be used as a dependency in route handlers.
    """
    
    def __init__(self, request: Request):
        """Initialize the task dependency.
        
        Args:
            request: The current request object.
        """
        self.request = request
        self.task_manager = request.base_app.task_manager
        self.logger = logging.getLogger("nexios.tasks")
    
    async def create(
        self,
        func: TaskCallback,
        *args: Any,
        name: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs: Any
    ) -> Task:
        """Create and schedule a new background task.
        
        Args:
            func: The coroutine function to execute.
            *args: Positional arguments to pass to the function.
            name: Optional name for the task.
            timeout: Optional timeout in seconds.
            **kwargs: Keyword arguments to pass to the function.
            
        Returns:
            The created task instance.
        """
        return await self.task_manager.create_task(
            func=func,
            *args,
            name=name,
            timeout=timeout,
            **kwargs
        )
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by its ID.
        
        Args:
            task_id: The ID of the task to retrieve.
            
        Returns:
            The task instance, or None if not found.
        """
        return self.task_manager.get_task(task_id)
    
    async def wait_for_task(
        self,
        task_id: str,
        timeout: Optional[float] = None
    ) -> Any:
        """Wait for a task to complete and return its result.
        
        Args:
            task_id: The ID of the task to wait for.
            timeout: Optional timeout in seconds.
            
        Returns:
            The result of the task.
            
        Raises:
            asyncio.TimeoutError: If the task times out.
            Exception: If the task raises an exception.
        """
        return await self.task_manager.wait_for_task(task_id, timeout=timeout)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task.
        
        Args:
            task_id: The ID of the task to cancel.
            
        Returns:
            True if the task was cancelled, False otherwise.
        """
        return await self.task_manager.cancel_task(task_id)


def get_task_dependency(
    request =  Context().request,
) -> TaskDepend:
    """Dependency function to get a TaskDepend instance.
    
    This is the recommended way to get a TaskDepend instance in route handlers.
    """
    return TaskDepend(request)


def TaskDependency() -> TaskDepend:
    return Depend(get_task_dependency)
    

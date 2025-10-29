"""
Task manager implementation for Nexios.

This module provides the TaskManager class which is responsible for managing
background tasks in a Nexios application.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Union

from nexios import NexiosApp

from .config import TaskConfig, TaskStatus
from .models import Task, TaskResult, TaskError
import time

T = TypeVar('T')
TaskCallback = Callable[..., Awaitable[Any]]
TaskResultCallback = Callable[[str, Any, Optional[Exception]], Awaitable[None]]

class TaskManager:
    """Manages background tasks for Nexios applications.
    
    This class provides methods to create, monitor, and manage background tasks.
    It's designed to be used as a singleton per application instance.
    """
    
    def __init__(self, app: Optional[NexiosApp] = None, config: Optional[TaskConfig] = None) -> None:
        """Initialize the task manager.
        
        Args:
            app: The Nexios application instance.
            config: Configuration for the task manager.
        """
        self.app = app
        self.config = config or TaskConfig()
        self.tasks: Dict[str, Task] = {}
        self._shutdown = False
        self._task_callbacks: Dict[str, List[TaskResultCallback]] = {}
        self.logger = logging.getLogger("nexios.tasks")
        
        # Configure logging
        logging.basicConfig(level=self.config.log_level)
    
    async def start(self) -> None:
        """Initialize the task manager.
        
        This method should be called during application startup.
        """
        if self.app is not None:
            self.app.on_shutdown(self.shutdown)
        self.logger.info("Task manager started")
    
    async def shutdown(self) -> None:
        """Shutdown the task manager and cancel all running tasks.
        
        This method is automatically called during application shutdown.
        """
        self._shutdown = True
        self.logger.info("Shutting down task manager...")
        
        # Cancel all running tasks
        tasks_to_cancel = [task for task in self.tasks.values() 
                          if task._task and not task.is_done]
        
        if tasks_to_cancel:
            self.logger.info("Cancelling %d running tasks...", len(tasks_to_cancel))
            for task in tasks_to_cancel:
                if task._task:
                    task._task.cancel()
            
            # Wait for tasks to complete cancellation
            await asyncio.gather(
                *(task._task for task in tasks_to_cancel if task._task),
                return_exceptions=True
            )
        
        self.logger.info("Task manager shutdown complete")
    
    async def create_task(
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
            
        Raises:
            RuntimeError: If the task manager is shutting down.
            asyncio.TimeoutError: If the task times out.
        """
        if self._shutdown:
            raise RuntimeError("Cannot create new tasks during shutdown")
        
        # Create the task
        task = Task(func, *args, name=name or func.__name__, **kwargs)
        self.tasks[task.id] = task
        
        # Create the asyncio task
        task._task = asyncio.create_task(self._run_task(task, timeout))
        
        self.logger.debug("Created task %s (ID: %s)", task.name, task.id)
        return task
    
    async def _run_task(self, task: Task, timeout: Optional[float] = None) -> None:
        """Internal method to run a task and handle its completion."""
        try:
            # Use the configured timeout if none provided
            timeout = timeout or self.config.default_timeout
            
            if timeout is not None:
                # Run with timeout if specified
                await asyncio.wait_for(task.run(), timeout=timeout)
            else:
                # Run without timeout
                await task.run()
                
            self.logger.debug("Task %s completed successfully", task.id)
            
        except asyncio.CancelledError:
            # Task was cancelled
            self.logger.debug("Task %s was cancelled", task.id)
            task._status = TaskStatus.CANCELLED
            task._result = TaskResult(
                task_id=task.id,
                result=None,
                status=TaskStatus.CANCELLED,
                error=asyncio.CancelledError("Task was cancelled"),
                completed_at=time.time()
            )
            if task.id in self.tasks:
                del self.tasks[task.id]
            raise
            
        except asyncio.TimeoutError:
            # Task timed out
            error_msg = f"Task {task.id} timed out after {timeout} seconds"
            self.logger.warning(error_msg)
            task._status = TaskStatus.FAILED
            task._result = TaskResult(
                task_id=task.id,
                result=None,
                status=TaskStatus.FAILED,
                error=TimeoutError(error_msg),
                completed_at=time.time()
            )
            
        except Exception as e:
            # Task failed with an exception
            self.logger.exception("Task %s failed with error: %s", task.id, str(e))
            task._status = TaskStatus.FAILED
            task._result = TaskResult(
                task_id=task.id,
                result=None,
                status=TaskStatus.FAILED,
                error=e,
                completed_at=time.time()
            )
            
        finally:
            # Ensure the task is marked as done
            task._completed_at = time.time()
            if hasattr(task, '_done_event'):
                task._done_event.set()
            
            # Execute any registered callbacks
            await self._execute_callbacks(task)
            
            # Clean up if needed
            if not self.config.enable_task_history and task.id in self.tasks:
                del self.tasks[task.id]
    
    async def _execute_callbacks(self, task: Task) -> None:
        """Execute all registered callbacks for a task."""
        if task.id not in self._task_callbacks:
            return
            
        for callback in self._task_callbacks[task.id]:
            try:
                await callback(task.id, task._result, task._result.error if task._result else None)
            except Exception as e:
                self.logger.exception("Error in task callback for %s: %s", task.id, str(e))
        
        # Clean up callbacks
        del self._task_callbacks[task.id]
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by its ID.
        
        Args:
            task_id: The ID of the task to retrieve.
            
        Returns:
            The task instance, or None if not found.
        """
        return self.tasks.get(task_id)
    
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
            ValueError: If the task ID is not found.
            asyncio.TimeoutError: If the task times out.
            Exception: If the task raises an exception.
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
            
        return await task.wait(timeout=timeout)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task.
        
        Args:
            task_id: The ID of the task to cancel.
            
        Returns:
            True if the task was cancelled, False otherwise.
        """
        task = self.get_task(task_id)
        if not task or not task._task or task.is_done:
            return False
            
        task._task.cancel()
        return True
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """Get a list of all tasks, optionally filtered by status.
        
        Args:
            status: Optional status to filter tasks by.
            
        Returns:
            A list of tasks matching the criteria.
        """
        if status is None:
            return list(self.tasks.values())
        return [task for task in self.tasks.values() if task.status == status]
    
    def add_callback(
        self, 
        task: Union[str, Task], 
        callback: TaskResultCallback
    ) -> None:
        """Add a callback to be called when a task completes.
        
        Args:
            task_id: The ID of the task to add the callback to.
            callback: The callback function to call when the task completes.
            
        Raises:
            ValueError: If the task ID is not found.
        """
        if isinstance(task, Task):
            task = task.id
        if task not in self.tasks:
            raise ValueError(f"Task {task} not found")
            
        if task not in self._task_callbacks:
            self._task_callbacks[task] = []
            
        self._task_callbacks[task].append(callback)
    
    def remove_callback(
        self, 
        task_id: str, 
        callback: TaskResultCallback
    ) -> bool:
        """Remove a callback from a task.
        
        Args:
            task_id: The ID of the task to remove the callback from.
            callback: The callback function to remove.
            
        Returns:
            True if the callback was removed, False otherwise.
        """
        if task_id not in self._task_callbacks:
            return False
            
        try:
            self._task_callbacks[task_id].remove(callback)
            return True
        except ValueError:
            return False

"""
Nexios Tasks - Background Task Management for Nexios

This module provides a robust and efficient way to manage background tasks in Nexios applications.
It includes features like task lifecycle management, error handling, and result callbacks.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Union

from nexios import NexiosApp
from nexios.dependencies import Depend
from nexios.http import Request

from .config import TaskConfig, TaskStatus
from .dependency import TaskDepend, TaskDependency, get_task_dependency
from .manager import TaskManager
from .models import Task, TaskError, TaskResult

# Re-export public API
__all__ = [
    # Main classes
    'Task',
    'TaskManager',
    'TaskConfig',
    'TaskStatus',
    'TaskResult',
    'TaskError',
    
    # Dependency injection
    'TaskDepend',
    'TaskDependency',
    'get_task_dependency',
    
    # Utility functions
    'setup_tasks',
    'get_task_manager',
    'create_task',
]

# Type variables for generic type hints
T = TypeVar('T')
TaskCallback = Callable[..., Awaitable[Any]]
TaskResultCallback = Callable[[str, Any, Optional[Exception]], Awaitable[None]]

def setup_tasks(
    app: NexiosApp,
    config: Optional[TaskConfig] = None
) -> TaskManager:
    """Set up the task manager for a Nexios application.
    
    This function initializes the task manager and registers it with the Nexios app.
    It should be called during application startup.
    
    Args:
        app: The Nexios application instance.
        config: Optional configuration for the task manager.
        
    Returns:
        The initialized TaskManager instance.
        
    Example:
        ```python
        from nexios import NexiosApp
        from nexios_contrib.tasks import setup_tasks, TaskConfig
        
        app = NexiosApp()
        
        # Initialize with default configuration
        task_manager = setup_tasks(app)
        
        # Or with custom configuration
        config = TaskConfig(
            max_concurrent_tasks=50,
            default_timeout=300,  # 5 minutes
            enable_task_history=True
        )
        task_manager = setup_tasks(app, config=config)
        ```
    """
    if not hasattr(app, 'task_manager'):
        task_manager = TaskManager(app, config=config)
        app.task_manager = task_manager
        app.on_startup(task_manager.start)
    return app.task_manager

def get_task_manager(request: Request) -> TaskManager:
    """Get the task manager from a request.
    
    This is a convenience function to get the task manager instance
    from a request object.
    
    Args:
        request: The current request object.
        
    Returns:
        The TaskManager instance.
        
    Raises:
        AttributeError: If the task manager is not initialized.
        
    Example:
        ```python
        from nexios import Request
        from nexios_contrib.tasks import get_task_manager
        
        @app.get("/tasks/{task_id}")
        async def get_task_status(request: Request):
            task_manager = get_task_manager(request)
            task_id = request.path_params["task_id"]
            task = task_manager.get_task(task_id)
            return {"status": task.status if task else "not_found"}
        ```
    """
    task_manager = getattr(request.base_app, 'task_manager', None)
    if task_manager is None:
        raise AttributeError(
            "Task manager not initialized. Call setup_tasks(app) during application startup."
        )
    return task_manager

def create_task(
    request: Request,
    func: TaskCallback,
    *args: Any,
    name: Optional[str] = None,
    timeout: Optional[float] = None,
    **kwargs: Any
) -> Task:
    """Create and schedule a new background task.
    
    This is a convenience function that gets the task manager from the request
    and creates a new task with the given function and arguments.
    
    Args:
        request: The current request object.
        func: The coroutine function to execute in the background.
        *args: Positional arguments to pass to the function.
        name: Optional name for the task (for identification).
        timeout: Optional timeout in seconds for the task.
        **kwargs: Keyword arguments to pass to the function.
        
    Returns:
        The created Task instance.
        
    Example:
        ```python
        from nexios import Request
        from nexios_contrib.tasks import create_task
        
        async def process_data(data: dict) -> dict:
            # Long-running processing
            await asyncio.sleep(5)
            return {"processed": True, **data}
            
        @app.post("/process")
        async def start_processing(request: Request):
            data = await request.json()
            task = create_task(
                request,
                process_data,
                data,
                name=f"process_{data.get('id')}",
                timeout=60  # 1 minute timeout
            )
            return {"task_id": task.id}
        ```
    """
    task_manager = get_task_manager(request)
    return task_manager.create_task(
        func=func,
        *args,
        name=name,
        timeout=timeout,
        **kwargs
    )

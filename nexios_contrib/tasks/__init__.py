"""
Nexios Tasks - Background Task Management for Nexios

This module provides a robust and efficient way to manage background tasks in Nexios applications.
It includes features like task lifecycle management, error handling, and result callbacks.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Union, cast

from nexios import NexiosApp
from nexios.dependencies import Depend, current_context
from nexios.http import Request
import warnings

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
    request_or_func: Union[Request, TaskCallback],
    func_or_arg: Optional[Union[TaskCallback, Any]] = None,
    *args: Any,
    name: Optional[str] = None,
    timeout: Optional[float] = None,
    **kwargs: Any
) -> Task:
    """Create and schedule a new background task.
    
    This function creates a new background task. It can be called in two ways:
    
    1. New (Recommended): create_task(func, *args, **kwargs)
       The request/task manager is automatically resolved from the current context.
       
    2. Deprecated: create_task(request, func, *args, **kwargs)
       Explicitly passing the request object.
    
    Args:
        request_or_func: Context request or the task function.
        func_or_arg: Task function (if request passed first) or first task argument.
        *args: Additional positional arguments for the task.
        name: Optional name for the task.
        timeout: Optional timeout in seconds.
        **kwargs: Keyword arguments for the task.
        
    Returns:
        The created Task instance.
    """
    request: Optional[Request] = None
    func: TaskCallback
    task_args: List[Any] = []

    # Check for legacy usage: create_task(request, func, ...)
    # We check if the first argument looks like a Request (not callable)
    if not callable(request_or_func) and hasattr(request_or_func, "base_app"):
        warnings.warn(
            "Passing 'request' to create_task is deprecated and will be removed in a future version. "
            "Please use 'create_task(func, *args)' directly, as the context is now automatically resolved.",
            DeprecationWarning,
            stacklevel=2,
        )
        request = cast(Request, request_or_func)
        
        if func_or_arg is None or not callable(func_or_arg):
             raise ValueError("When passing request explicitly, the second argument must be a callable task function.")
        
        func = cast(TaskCallback, func_or_arg)
        task_args = list(args)

    else:
        # New usage: create_task(func, arg1, arg2...)
        func = cast(TaskCallback, request_or_func)
        
        # In this mode, func_or_arg is actually the first argument for the task (if present)
        if func_or_arg is not None:
            task_args = [func_or_arg] + list(args)
        else:
            task_args = list(args)
            
        # Resolve request from context
        try:
            ctx = current_context.get()
            if ctx and ctx.request:
                request = ctx.request
        except LookupError:
            pass

    if request is None:
        raise RuntimeError(
            "Could not resolve active request context. "
            "Ensure you are calling create_task within a Nexios request context, "
            "or pass the request explicitly (deprecated)."
        )

    task_manager = get_task_manager(request)
    return task_manager.create_task(
        func=func,
        *task_args,
        name=name,
        timeout=timeout,
        **kwargs
    )

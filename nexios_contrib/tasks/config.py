"""
Task module configuration for Nexios.

This module provides configuration options for the task management system.
"""
from typing import Optional, Dict, Any, Union, List, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import logging

class TaskStatus(str, Enum):
    """Status of a background task."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

@dataclass
class TaskConfig:
    """Configuration for the task manager.
    
    Attributes:
        max_concurrent_tasks: Maximum number of tasks that can run concurrently.
        default_timeout: Default timeout in seconds for tasks.
        task_result_ttl: Time in seconds to keep task results after completion.
        enable_task_history: Whether to keep a history of completed tasks.
        log_level: Logging level for task-related logs.
    """
    max_concurrent_tasks: int = 100
    default_timeout: Optional[float] = None
    task_result_ttl: int = 3600  # 1 hour
    enable_task_history: bool = True
    log_level: int = logging.INFO
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return {
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "default_timeout": self.default_timeout,
            "task_result_ttl": self.task_result_ttl,
            "enable_task_history": self.enable_task_history,
            "log_level": self.log_level,
        }

# Default configuration
DEFAULT_CONFIG = TaskConfig()

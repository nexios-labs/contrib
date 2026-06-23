"""
Nexios Scheduler - Job Scheduling for Nexios

Provides interval-based, cron-based, and one-time job scheduling
integrated with the Nexios application lifecycle and dependency injection.
"""

from __future__ import annotations

from typing import Optional

from nexios import NexiosApp

from .config import (
    CronTrigger,
    DateTimeTrigger,
    IntervalTrigger,
    JobStatus,
    SchedulerConfig,
)
from .dependency import SchedulerDepend, SchedulerDepends
from .manager import SchedulerManager
from .models import JobCallback, ScheduledJob

__all__ = [
    # Main classes
    "SchedulerManager",
    "ScheduledJob",
    "SchedulerConfig",
    "JobStatus",
    # Triggers
    "IntervalTrigger",
    "CronTrigger",
    "DateTimeTrigger",
    # Dependency injection
    "SchedulerDepend",
    "SchedulerDepends",
    # Utility functions
    "setup_scheduler",
    "get_scheduler",
]


def setup_scheduler(
    app: NexiosApp, config: Optional[SchedulerConfig] = None
) -> SchedulerManager:
    """Set up the scheduler for a Nexios application.

    Initialises the ``SchedulerManager``, attaches it as ``app.scheduler``,
    and registers the startup hook.

    Args:
        app: The Nexios application instance.
        config: Optional scheduler configuration.

    Returns:
        The initialised ``SchedulerManager`` instance.

    Example::

        from nexios import NexiosApp
        from nexios_contrib.scheduler import (
            setup_scheduler,
            IntervalTrigger,
        )

        app = NexiosApp()
        scheduler = setup_scheduler(app)

        async def my_task():
            print("tick")

        scheduler.add_job(my_task, IntervalTrigger(seconds=30))
    """
    if not hasattr(app, "scheduler"):
        scheduler = SchedulerManager(app, config=config)
        app.scheduler = scheduler  # ty:ignore[invalid-assignment]
        app.on_startup(scheduler.start)
    return app.scheduler  # ty:ignore[unresolved-attribute]


def get_scheduler(app: NexiosApp) -> SchedulerManager:
    """Retrieve the scheduler instance from a Nexios app.

    Args:
        app: The Nexios application instance.

    Returns:
        The ``SchedulerManager`` instance.

    Raises:
        AttributeError: If the scheduler has not been initialised.
    """
    scheduler = getattr(app, "scheduler", None)
    if scheduler is None:
        raise AttributeError(
            "Scheduler not initialised. Call setup_scheduler(app) during app setup."
        )
    return scheduler

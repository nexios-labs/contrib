"""
Dependency injection for the Nexios scheduler.

Provides a ``SchedulerDepend`` class and a ``SchedulerDepends`` callable
that can be used as a route dependency in Nexios handlers.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, cast

from nexios.dependencies import Context, Depend
from nexios.http import Request

from .config import CronTrigger, DateTimeTrigger, IntervalTrigger, JobStatus
from .manager import SchedulerManager
from .models import JobCallback, ScheduledJob


class SchedulerDepend:
    """Injectable dependency that exposes scheduler operations.

    Use via ``SchedulerDepends()`` in your route handler signature.
    """

    def __init__(self, request: Request) -> None:
        self.request = request
        self.scheduler: SchedulerManager = request.base_app.scheduler  # ty:ignore[unresolved-attribute]

    def add_job(
        self,
        func: JobCallback,
        trigger: IntervalTrigger | CronTrigger | DateTimeTrigger,
        *,
        name: Optional[str] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        max_instances: Optional[int] = None,
        misfire_grace_time: Optional[int] = None,
        coalesce: Optional[bool] = None,
        id: Optional[str] = None,
    ) -> ScheduledJob:
        """Register a new scheduled job from within a route handler."""
        return self.scheduler.add_job(
            func=func,
            trigger=trigger,
            name=name,
            args=args,
            kwargs=kwargs,
            max_instances=max_instances,
            misfire_grace_time=misfire_grace_time,
            coalesce=coalesce,
            id=id,
        )

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job."""
        return self.scheduler.remove_job(job_id)

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Get a scheduled job by id."""
        return self.scheduler.get_job(job_id)

    def get_jobs(self, status: Optional[JobStatus] = None) -> List[ScheduledJob]:
        """List all scheduled jobs, optionally filtered by status."""
        return self.scheduler.get_jobs(status=status)

    def pause_job(self, job_id: str) -> bool:
        """Pause a scheduled job."""
        return self.scheduler.pause_job(job_id)

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        return self.scheduler.resume_job(job_id)


def _get_scheduler_depend(ctx: Context = Context()) -> SchedulerDepend:
    """Factory used by the ``SchedulerDepends`` callable."""
    
    return SchedulerDepend(ctx.request)  # ty:ignore[invalid-argument-type]


def SchedulerDepends() -> SchedulerDepend:
    return cast(typ=SchedulerDepend, val=Depend(_get_scheduler_depend))
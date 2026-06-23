"""
Data models for the scheduler system.

This module defines the Job class that represents a scheduled task
along with its trigger configuration and execution state.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar
from uuid import uuid4

from .config import (
    CronTrigger,
    DateTimeTrigger,
    IntervalTrigger,
    JobStatus,
    TriggerType,
)

T = TypeVar("T")
JobCallback = Callable[..., Awaitable[Any]]


class ScheduledJob:
    """Represents a scheduled job.

    Encapsulates the callable, trigger, and runtime state of a job
    managed by the scheduler.
    """

    def __init__(
        self,
        func: JobCallback,
        trigger: IntervalTrigger | CronTrigger | DateTimeTrigger,
        *,
        name: Optional[str] = None,
        args: Optional[tuple[Any, ...]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        max_instances: int = 3,
        misfire_grace_time: int = 30,
        coalesce: bool = True,
        id: Optional[str] = None,
    ) -> None:
        self.id = id or str(uuid4())
        self.name = name or func.__name__  # ty:ignore[unresolved-attribute]
        self.func = func
        self.trigger = trigger
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.max_instances = max_instances
        self.misfire_grace_time = misfire_grace_time
        self.coalesce = coalesce

        self._status: JobStatus = JobStatus.ACTIVE
        self._created_at = time.time()
        self._last_run_time: Optional[float] = None
        self._next_run_time: Optional[float] = None
        self._current_instances: int = 0
        self._total_run_count: int = 0
        self._last_error: Optional[str] = None
        self._logger = logging.getLogger("nexios.scheduler.job")

    # --- Properties ---

    @property
    def status(self) -> JobStatus:
        return self._status

    @property
    def created_at(self) -> float:
        return self._created_at

    @property
    def last_run_time(self) -> Optional[float]:
        return self._last_run_time

    @property
    def next_run_time(self) -> Optional[float]:
        return self._next_run_time

    @property
    def total_run_count(self) -> int:
        return self._total_run_count

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    @property
    def current_instances(self) -> int:
        return self._current_instances

    # --- Public API ---

    def compute_next_run(self, from_timestamp: Optional[float] = None) -> None:
        """Calculate and store the next scheduled run time."""
        from_ts = from_timestamp if from_timestamp is not None else time.time()

        if isinstance(self.trigger, IntervalTrigger):
            if self._last_run_time is None and self.trigger.start_now:
                self._next_run_time = from_ts
            else:
                last = self._last_run_time or from_ts
                self._next_run_time = last + self.trigger.as_seconds()

        elif isinstance(self.trigger, CronTrigger):
            self._next_run_time = self.trigger.get_next_run(from_ts)

        elif isinstance(self.trigger, DateTimeTrigger):
            self._next_run_time = self.trigger.get_run_timestamp()

    async def run(self) -> Any:
        """Execute the job function and return its result."""
        if self._status == JobStatus.CANCELLED:
            raise RuntimeError(f"Job {self.id} has been cancelled")

        self._current_instances += 1
        self._total_run_count += 1
        self._last_run_time = time.time()
        self._status = JobStatus.ACTIVE

        try:
            result = await self.func(*self.args, **self.kwargs)
            return result
        except Exception as exc:
            self._last_error = str(exc)
            self._status = JobStatus.FAILED
            self._logger.exception("Job %s (%s) failed: %s", self.id, self.name, exc)
            raise
        finally:
            self._current_instances -= 1

    def pause(self) -> None:
        """Pause this job. It will not fire until resumed."""
        self._status = JobStatus.PAUSED

    def resume(self) -> None:
        """Resume a paused job."""
        self._status = JobStatus.ACTIVE

    def cancel(self) -> None:
        """Cancel this job permanently."""
        self._status = JobStatus.CANCELLED
        self._next_run_time = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the job state to a dictionary."""
        trigger_type = TriggerType.INTERVAL
        trigger_repr = ""
        if isinstance(self.trigger, IntervalTrigger):
            trigger_type = TriggerType.INTERVAL
            trigger_repr = f"{self.trigger.as_seconds()}s"
        elif isinstance(self.trigger, CronTrigger):
            trigger_type = TriggerType.CRON
            trigger_repr = self.trigger.expr
        elif isinstance(self.trigger, DateTimeTrigger):
            trigger_type = TriggerType.DATETIME
            trigger_repr = self.trigger.run_date

        return {
            "id": self.id,
            "name": self.name,
            "status": self._status.value,
            "trigger_type": trigger_type.value,
            "trigger": trigger_repr,
            "total_run_count": self._total_run_count,
            "current_instances": self._current_instances,
            "created_at": self._created_at,
            "last_run_time": self._last_run_time,
            "next_run_time": self._next_run_time,
            "last_error": self._last_error,
            "max_instances": self.max_instances,
            "coalesce": self.coalesce,
        }

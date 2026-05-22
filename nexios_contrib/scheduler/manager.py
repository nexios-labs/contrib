"""
Scheduler manager for Nexios.

This module provides the SchedulerManager class which is responsible for
managing scheduled jobs and their execution lifecycle in a Nexios application.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from nexios import NexiosApp

from .config import (
    CronTrigger,
    DateTimeTrigger,
    IntervalTrigger,
    JobStatus,
    SchedulerConfig,
)
from .models import JobCallback, ScheduledJob


class SchedulerManager:
    """Manages scheduled jobs for Nexios applications.

    Handles job registration, scheduling, lifecycle management, and
    coordination with the Nexios app lifecycle (startup/shutdown).
    """

    def __init__(
        self, app: Optional[NexiosApp] = None, config: Optional[SchedulerConfig] = None
    ) -> None:
        self.app = app
        self.config = config or SchedulerConfig()
        self._jobs: Dict[str, ScheduledJob] = {}
        self._running = False
        self._ticker_task: Optional[asyncio.Task] = None
        self._logger = logging.getLogger("nexios.scheduler")

        logging.basicConfig(level=self.config.log_level)

    # --- Lifecycle ---

    async def start(self) -> None:
        """Start the scheduler.

        Registers shutdown hook if an app is attached and begins the
        background ticker loop.
        """
        if self._running:
            self._logger.warning("Scheduler is already running")
            return

        self._running = True

        if self.app is not None:
            self.app.on_shutdown(self.shutdown)

        # Compute initial next run times for all active jobs
        now = time.time()
        for job in self._jobs.values():
            if job.status == JobStatus.ACTIVE:
                job.compute_next_run(now)

        self._ticker_task = asyncio.create_task(self._ticker_loop())
        self._logger.info("Scheduler started with %d active job(s)", self._active_count)

    async def shutdown(self) -> None:
        """Gracefully shut down the scheduler.

        Cancels the ticker loop and cancels all active jobs.
        """
        if not self._running:
            return

        self._running = False
        self._logger.info("Shutting down scheduler...")

        if self._ticker_task and not self._ticker_task.done():
            self._ticker_task.cancel()
            try:
                await self._ticker_task
            except asyncio.CancelledError:
                pass

        # Cancel all active/paused jobs
        for job in self._jobs.values():
            if job.status in (JobStatus.ACTIVE, JobStatus.PAUSED):
                job.cancel()

        self._logger.info("Scheduler shutdown complete")

    # --- Job Management ---

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
        """Register a new scheduled job.

        Args:
            func: Async callable to execute.
            trigger: One of ``IntervalTrigger``, ``CronTrigger``, or
                ``DateTimeTrigger``.
            name: Human-readable name (defaults to ``func.__name__``).
            args: Positional arguments passed to ``func``.
            kwargs: Keyword arguments passed to ``func``.
            max_instances: Override the default from config.
            misfire_grace_time: Override the default from config.
            coalesce: Override the default from config.
            id: Explicit job ID (auto-generated if omitted).

        Returns:
            The newly created ``ScheduledJob`` instance.
        """
        job = ScheduledJob(
            func=func,
            trigger=trigger,
            name=name,
            args=args or (),
            kwargs=kwargs or {},
            max_instances=max_instances or self.config.job_defaults.get("max_instances", 3),
            misfire_grace_time=misfire_grace_time
                or self.config.job_defaults.get("misfire_grace_time", 30),
            coalesce=coalesce or self.config.job_defaults.get("coalesce", True),
            id=id,
        )

        self._jobs[job.id] = job

        if self._running:
            job.compute_next_run()

        self._logger.info(
            "Added job %s (%s) with trigger %s",
            job.id,
            job.name,
            type(trigger).__name__,
        )
        return job

    def remove_job(self, job_id: str) -> bool:
        """Remove a job from the scheduler.

        Returns:
            True if the job was found and removed, False otherwise.
        """
        job = self._jobs.pop(job_id, None)
        if job is None:
            return False
        job.cancel()
        self._logger.debug("Removed job %s (%s)", job_id, job.name)
        return True

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Look up a job by its id."""
        return self._jobs.get(job_id)

    def get_jobs(self, status: Optional[JobStatus] = None) -> List[ScheduledJob]:
        """List registered jobs, optionally filtered by status."""
        if status is None:
            return list(self._jobs.values())
        return [j for j in self._jobs.values() if j.status == status]

    def pause_job(self, job_id: str) -> bool:
        """Pause a job so it won't fire.

        Returns:
            True if the job was found and paused.
        """
        job = self._jobs.get(job_id)
        if job is None:
            return False
        job.pause()
        self._logger.debug("Paused job %s (%s)", job_id, job.name)
        return True

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job.

        Returns:
            True if the job was found and resumed.
        """
        job = self._jobs.get(job_id)
        if job is None:
            return False
        job.resume()
        job.compute_next_run()
        self._logger.debug("Resumed job %s (%s)", job_id, job.name)
        return True

    # --- Internal ---

    @property
    def _active_count(self) -> int:
        return sum(
            1 for j in self._jobs.values() if j.status == JobStatus.ACTIVE
        )

    async def _ticker_loop(self) -> None:
        """Background loop that checks every second for due jobs."""
        self._logger.debug("Ticker loop started (tick=1s)")

        try:
            while self._running:
                now = time.time()
                due = self._get_due_jobs(now)

                for job in due:
                    asyncio.ensure_future(self._execute_job(job))

                await asyncio.sleep(1)
        except asyncio.CancelledError:
            self._logger.debug("Ticker loop cancelled")
        except Exception:
            self._logger.exception("Ticker loop crashed")
            raise

    def _get_due_jobs(self, now: float) -> List[ScheduledJob]:
        """Return all jobs that are due to run at ``now``."""
        due: List[ScheduledJob] = []

        for job in self._jobs.values():
            if job.status != JobStatus.ACTIVE:
                continue
            if job.next_run_time is None:
                continue

            if job.next_run_time <= now:
                # Check misfire grace window
                misfire = job.misfire_grace_time
                if misfire >= 0 and now - job.next_run_time > misfire:
                    self._logger.warning(
                        "Job %s (%s) misfired (scheduled: %s, now: %s)",
                        job.id,
                        job.name,
                        job.next_run_time,
                        now,
                    )
                    job.compute_next_run(now)
                    continue

                # Check max concurrent instances
                if job.current_instances >= job.max_instances:
                    self._logger.debug(
                        "Job %s (%s) at max instances (%s), skipping",
                        job.id,
                        job.name,
                        job.max_instances,
                    )
                    continue

                due.append(job)
                job.compute_next_run(now)

        return due

    async def _execute_job(self, job: ScheduledJob) -> None:
        """Execute a single job and handle errors."""
        try:
            await job.run()
        except asyncio.CancelledError:
            raise
        except Exception:
            self._logger.exception("Job %s (%s) raised an exception", job.id, job.name)
        finally:
            # For one-shot DateTimeTrigger jobs, mark as completed
            if isinstance(job.trigger, DateTimeTrigger):
                job._status = JobStatus.COMPLETED  # type: ignore[attr-defined]
                self._logger.debug("One-shot job %s completed", job.id)

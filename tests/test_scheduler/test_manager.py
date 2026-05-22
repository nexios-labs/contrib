"""
Tests for the SchedulerManager class.
"""
import asyncio

import pytest

from nexios import NexiosApp

from nexios_contrib.scheduler.config import (
    CronTrigger,
    DateTimeTrigger,
    IntervalTrigger,
    JobStatus,
    SchedulerConfig,
)
from nexios_contrib.scheduler.manager import SchedulerManager


@pytest.fixture
def app():
    return NexiosApp()


@pytest.fixture
def scheduler(app):
    return SchedulerManager(app)


@pytest.fixture
async def running_scheduler(scheduler):
    await scheduler.start()
    yield scheduler
    await scheduler.shutdown()


class TestSchedulerManager:
    def test_initial_state(self, scheduler):
        assert scheduler._running is False
        assert len(scheduler._jobs) == 0

    def test_add_interval_job(self, scheduler):
        async def my_task():
            pass

        job = scheduler.add_job(my_task, IntervalTrigger(seconds=60))
        assert job is not None
        assert job.id in scheduler._jobs
        assert len(scheduler._jobs) == 1

    def test_add_cron_job(self, scheduler):
        async def my_task():
            pass

        job = scheduler.add_job(my_task, CronTrigger("* * * * *"))
        assert job is not None
        assert job.id in scheduler._jobs

    def test_add_datetime_job(self, scheduler):
        async def my_task():
            pass

        job = scheduler.add_job(my_task, DateTimeTrigger("2030-01-01T00:00:00"))
        assert job is not None
        assert job.id in scheduler._jobs

    def test_remove_job(self, scheduler):
        async def my_task():
            pass

        job = scheduler.add_job(my_task, IntervalTrigger(seconds=60))
        assert len(scheduler._jobs) == 1

        result = scheduler.remove_job(job.id)
        assert result is True
        assert len(scheduler._jobs) == 0

    def test_remove_nonexistent_job(self, scheduler):
        result = scheduler.remove_job("nonexistent")
        assert result is False

    def test_get_job(self, scheduler):
        async def my_task():
            pass

        job = scheduler.add_job(my_task, IntervalTrigger(seconds=60))
        retrieved = scheduler.get_job(job.id)
        assert retrieved is job

    def test_get_nonexistent_job(self, scheduler):
        assert scheduler.get_job("nonexistent") is None

    def test_get_jobs(self, scheduler):
        async def task_a():
            pass

        async def task_b():
            pass

        scheduler.add_job(task_a, IntervalTrigger(seconds=60))
        scheduler.add_job(task_b, CronTrigger("* * * * *"))

        all_jobs = scheduler.get_jobs()
        assert len(all_jobs) == 2

    def test_get_jobs_filtered(self, scheduler):
        async def task_a():
            pass

        async def task_b():
            pass

        job_a = scheduler.add_job(task_a, IntervalTrigger(seconds=60))
        scheduler.add_job(task_b, CronTrigger("* * * * *"))

        job_a.pause()
        active = scheduler.get_jobs(status=JobStatus.ACTIVE)
        paused = scheduler.get_jobs(status=JobStatus.PAUSED)

        assert len(active) == 1
        assert len(paused) == 1

    def test_pause_and_resume_job(self, scheduler):
        async def my_task():
            pass

        job = scheduler.add_job(my_task, IntervalTrigger(seconds=60))

        paused = scheduler.pause_job(job.id)
        assert paused is True
        assert job.status == JobStatus.PAUSED

        resumed = scheduler.resume_job(job.id)
        assert resumed is True
        assert job.status == JobStatus.ACTIVE

    def test_pause_nonexistent(self, scheduler):
        assert scheduler.pause_job("nonexistent") is False

    def test_resume_nonexistent(self, scheduler):
        assert scheduler.resume_job("nonexistent") is False

    @pytest.mark.asyncio
    async def test_start_and_shutdown(self, scheduler):
        async def my_task():
            await asyncio.sleep(0.1)
            return "done"

        scheduler.add_job(my_task, IntervalTrigger(seconds=60))
        assert scheduler._running is False

        await scheduler.start()
        assert scheduler._running is True

        await scheduler.shutdown()
        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_double_start(self, running_scheduler):
        await running_scheduler.start()
        assert running_scheduler._running is True

    @pytest.mark.asyncio
    async def test_job_execution_via_ticker(self):
        app = NexiosApp()
        scheduler = SchedulerManager(app, SchedulerConfig())

        executed = False

        async def my_task():
            nonlocal executed
            executed = True

        scheduler.add_job(my_task, IntervalTrigger(seconds=1, start_now=True))

        await scheduler.start()
        await asyncio.sleep(1.5)
        await scheduler.shutdown()

        assert executed, "Job should have been executed by the ticker"

    @pytest.mark.asyncio
    async def test_cron_job_schedules_next_run(self):
        app = NexiosApp()
        scheduler = SchedulerManager(app)

        async def my_task():
            pass

        job = scheduler.add_job(my_task, CronTrigger("* * * * *"))

        await scheduler.start()
        job.compute_next_run()
        assert job.next_run_time is not None
        assert job.next_run_time > 0

        await scheduler.shutdown()

    @pytest.mark.asyncio
    async def test_datetime_job_completes(self):
        app = NexiosApp()
        scheduler = SchedulerManager(app)

        executed = False

        async def my_task():
            nonlocal executed
            executed = True

        scheduler.add_job(my_task, DateTimeTrigger("2030-01-01T00:00:00"))

        await scheduler.start()
        await asyncio.sleep(0.5)
        await scheduler.shutdown()

        # DateTimeTrigger is in the future, should NOT have executed
        assert executed is False

    @pytest.mark.asyncio
    async def test_job_failure_logged(self):
        app = NexiosApp()
        scheduler = SchedulerManager(app)

        async def failing_task():
            raise RuntimeError("job failed")

        job = scheduler.add_job(failing_task, IntervalTrigger(seconds=1, start_now=True))

        await scheduler.start()
        await asyncio.sleep(1.5)
        await scheduler.shutdown()

        assert job.last_error == "job failed"
        assert job.status == JobStatus.FAILED

    @pytest.mark.asyncio
    async def test_max_instances_respected(self):
        app = NexiosApp()
        scheduler = SchedulerManager(app)

        running = asyncio.Event()
        proceed = asyncio.Event()
        call_count = 0

        async def slow_task():
            nonlocal call_count
            call_count += 1
            running.set()
            await proceed.wait()

        job = scheduler.add_job(
            slow_task,
            IntervalTrigger(seconds=1, start_now=True),
            max_instances=1,
        )

        await scheduler.start()
        await running.wait()
        await asyncio.sleep(0.1)

        # Force a tick: next_run_time should be set to now
        old_next = job.next_run_time
        job._next_run_time = 0  # type: ignore[attr-defined]
        await asyncio.sleep(1.5)

        proceed.set()
        await asyncio.sleep(0.2)
        await scheduler.shutdown()

        # Only 1 instance should have run (max_instances=1 prevented the second)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_multiple_jobs(self):
        app = NexiosApp()
        scheduler = SchedulerManager(app)

        results = []

        async def task_a():
            results.append("A")

        async def task_b():
            results.append("B")

        scheduler.add_job(task_a, IntervalTrigger(seconds=1, start_now=True))
        scheduler.add_job(task_b, IntervalTrigger(seconds=1, start_now=True))

        await scheduler.start()
        await asyncio.sleep(1.5)
        await scheduler.shutdown()

        assert "A" in results
        assert "B" in results

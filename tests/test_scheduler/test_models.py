"""
Tests for the scheduler models module.
"""

import time

import pytest

from nexios_contrib.scheduler.config import (
    CronTrigger,
    DateTimeTrigger,
    IntervalTrigger,
    JobStatus,
)
from nexios_contrib.scheduler.models import ScheduledJob


@pytest.fixture
def sample_job():
    async def my_task():
        return 42

    return ScheduledJob(
        func=my_task,
        trigger=IntervalTrigger(seconds=60),
        name="test-job",
    )


class TestScheduledJob:
    def test_initial_state(self, sample_job):
        assert sample_job.status == JobStatus.ACTIVE
        assert sample_job.total_run_count == 0
        assert sample_job.current_instances == 0
        assert sample_job.last_error is None
        assert sample_job.next_run_time is None
        assert sample_job.last_run_time is None

    def test_compute_next_run_interval(self, sample_job):
        sample_job.compute_next_run()
        assert sample_job.next_run_time is not None
        assert sample_job.next_run_time > 0

    def test_compute_next_run_cron(self):
        async def task():
            pass

        job = ScheduledJob(
            func=task,
            trigger=CronTrigger("*/5 * * * *"),
        )
        job.compute_next_run()
        assert job.next_run_time is not None
        assert job.next_run_time > time.time()

    def test_compute_next_run_datetime(self):
        async def task():
            pass

        job = ScheduledJob(
            func=task,
            trigger=DateTimeTrigger("2030-01-01T00:00:00"),
        )
        job.compute_next_run()
        assert job.next_run_time is not None
        assert job.next_run_time > time.time()

    def test_pause_and_resume(self, sample_job):
        sample_job.pause()
        assert sample_job.status == JobStatus.PAUSED

        sample_job.resume()
        assert sample_job.status == JobStatus.ACTIVE

    def test_cancel(self, sample_job):
        sample_job.cancel()
        assert sample_job.status == JobStatus.CANCELLED
        assert sample_job.next_run_time is None

    @pytest.mark.asyncio
    async def test_run(self, sample_job):
        result = await sample_job.run()
        assert result == 42
        assert sample_job.total_run_count == 1
        assert sample_job.last_run_time is not None

    @pytest.mark.asyncio
    async def test_run_failure(self):
        async def failing_task():
            raise ValueError("boom")

        job = ScheduledJob(
            func=failing_task,
            trigger=IntervalTrigger(seconds=60),
        )

        with pytest.raises(ValueError, match="boom"):
            await job.run()

        assert job.last_error == "boom"
        assert job.status == JobStatus.FAILED

    def test_to_dict(self, sample_job):
        d = sample_job.to_dict()
        assert d["id"] == sample_job.id
        assert d["name"] == "test-job"
        assert d["status"] == JobStatus.ACTIVE.value
        assert d["trigger_type"] == "INTERVAL"
        assert "trigger" in d
        assert d["total_run_count"] == 0

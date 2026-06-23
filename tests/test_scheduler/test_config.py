"""
Tests for the scheduler configuration module.
"""

import time
from datetime import datetime, timezone

import pytest

from nexios_contrib.scheduler.config import (
    CronTrigger,
    DateTimeTrigger,
    IntervalTrigger,
    JobStatus,
    SchedulerConfig,
    TriggerType,
)


class TestIntervalTrigger:
    def test_as_seconds(self):
        t = IntervalTrigger(seconds=30)
        assert t.as_seconds() == 30

        t = IntervalTrigger(minutes=2, seconds=15)
        assert t.as_seconds() == 135

        t = IntervalTrigger(hours=1, minutes=30)
        assert t.as_seconds() == 5400

        t = IntervalTrigger(days=1, hours=2)
        assert t.as_seconds() == 93600

    def test_zero_total_raises(self):
        with pytest.raises(ValueError, match="greater than 0"):
            IntervalTrigger(seconds=0, minutes=0)

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            IntervalTrigger(seconds=-5)


class TestCronTrigger:
    def test_every_minute(self):
        t = CronTrigger("* * * * *")
        now = time.time()
        next_run = t.get_next_run(now)
        assert next_run > now
        # Should be at most 60 seconds from now
        assert next_run - now <= 70

    def test_hourly(self):
        t = CronTrigger("0 * * * *")
        now = time.time()
        next_run = t.get_next_run(now)
        assert next_run > now

        dt = datetime.fromtimestamp(next_run, tz=timezone.utc)
        assert dt.minute == 0

    def test_daily_at_midnight(self):
        t = CronTrigger("0 0 * * *")
        now = time.time()
        next_run = t.get_next_run(now)
        dt = datetime.fromtimestamp(next_run, tz=timezone.utc)
        assert dt.hour == 0
        assert dt.minute == 0

    def test_invalid_expression(self):
        with pytest.raises(ValueError, match="5 fields"):
            CronTrigger("* * *")

        with pytest.raises(ValueError, match="5 fields"):
            CronTrigger("* * * * * *")

    def test_alias_every_minute(self):
        t = CronTrigger("@every_minute")
        assert t._fields is not None

    def test_hourly_alias(self):
        t = CronTrigger("@hourly")
        now = time.time()
        next_run = t.get_next_run(now)
        dt = datetime.fromtimestamp(next_run, tz=timezone.utc)
        assert dt.minute == 0

    def test_daily_alias(self):
        t = CronTrigger("@daily")
        now = time.time()
        next_run = t.get_next_run(now)
        dt = datetime.fromtimestamp(next_run, tz=timezone.utc)
        assert dt.hour == 0
        assert dt.minute == 0

    def test_range_expression(self):
        t = CronTrigger("0 9-17 * * *")
        now = time.time()
        next_run = t.get_next_run(now)
        dt = datetime.fromtimestamp(next_run, tz=timezone.utc)
        assert 9 <= dt.hour <= 17
        assert dt.minute == 0

    def test_step_values(self):
        t = CronTrigger("*/15 * * * *")
        now = time.time()
        next_run = t.get_next_run(now)
        dt = datetime.fromtimestamp(next_run, tz=timezone.utc)
        assert dt.minute % 15 == 0

    def test_list_values(self):
        t = CronTrigger("30 9,12,15 * * *")
        now = time.time()
        next_run = t.get_next_run(now)
        dt = datetime.fromtimestamp(next_run, tz=timezone.utc)
        assert dt.minute == 30
        assert dt.hour in (9, 12, 15)


class TestDateTimeTrigger:
    def test_future_datetime(self):
        t = DateTimeTrigger("2030-01-01T00:00:00")
        ts = t.get_run_timestamp()
        assert ts > time.time()

    def test_past_datetime(self):
        t = DateTimeTrigger("2020-01-01T00:00:00")
        ts = t.get_run_timestamp()
        assert ts < time.time()

    def test_parses_date_only(self):
        t = DateTimeTrigger("2030-06-15")
        ts = t.get_run_timestamp()
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        assert dt.month == 6
        assert dt.day == 15

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="parse"):
            DateTimeTrigger("not-a-date")


class TestJobStatus:
    def test_values(self):
        assert JobStatus.ACTIVE.value == "ACTIVE"
        assert JobStatus.PAUSED.value == "PAUSED"
        assert JobStatus.COMPLETED.value == "COMPLETED"
        assert JobStatus.FAILED.value == "FAILED"
        assert JobStatus.CANCELLED.value == "CANCELLED"


class TestSchedulerConfig:
    def test_defaults(self):
        config = SchedulerConfig()
        assert config.max_concurrent_jobs == 10
        assert config.log_level is not None
        assert config.job_defaults["max_instances"] == 3

    def test_to_dict(self):
        config = SchedulerConfig(timezone="UTC")
        d = config.to_dict()
        assert d["timezone"] == "UTC"
        assert d["max_concurrent_jobs"] == 10

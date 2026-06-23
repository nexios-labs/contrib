"""
Scheduler configuration for Nexios.

This module provides configuration options and enums for the scheduler system.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class JobStatus(str, Enum):
    """Status of a scheduled job."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TriggerType(str, Enum):
    """Type of trigger for a scheduled job."""

    INTERVAL = "INTERVAL"
    CRON = "CRON"
    DATETIME = "DATETIME"


@dataclass
class IntervalTrigger:
    """Trigger that fires at fixed intervals.

    Attributes:
        seconds: Number of seconds between runs.
        minutes: Number of minutes between runs.
        hours: Number of hours between runs.
        days: Number of days between runs.
        start_now: If True, the job runs immediately upon scheduling.
            Otherwise, it waits for the first interval to elapse.
    """

    seconds: int = 0
    minutes: int = 0
    hours: int = 0
    days: int = 0
    start_now: bool = True

    def __post_init__(self) -> None:
        if self.seconds < 0 or self.minutes < 0 or self.hours < 0 or self.days < 0:
            raise ValueError("Interval values must be non-negative")
        total = self.as_seconds()
        if total <= 0:
            raise ValueError("Total interval must be greater than 0 seconds")

    def as_seconds(self) -> float:
        """Return the total interval in seconds."""
        return self.days * 86400 + self.hours * 3600 + self.minutes * 60 + self.seconds


@dataclass
class CronTrigger:
    """Trigger that fires based on a cron expression.

    Supports standard 5-field cron expressions:
        minute hour day_of_month month day_of_week

    Each field supports:
        - Exact values: ``5``
        - Wildcards: ``*``
        - Ranges: ``1-5``
        - Step values: ``*/5``
        - Lists: ``1,3,5``
        - Combinations: ``1-5,10``

    Special strings:
        ``"@hourly"``, ``"@daily"``, ``"@weekly"``, ``"@monthly"``,
        ``"@yearly"``, ``"@every_minute"``

    Args:
        expr: Cron expression string (5-field or special alias).
    """

    expr: str

    def __post_init__(self) -> None:
        resolved = self._resolve_alias(self.expr)
        self._fields = self._parse_expression(resolved)

    @staticmethod
    def _resolve_alias(expr: str) -> str:
        aliases = {
            "@every_minute": "* * * * *",
            "@hourly": "0 * * * *",
            "@daily": "0 0 * * *",
            "@weekly": "0 0 * * 0",
            "@monthly": "0 0 1 * *",
            "@yearly": "0 0 1 1 *",
        }
        return aliases.get(expr, expr)

    @staticmethod
    def _parse_expression(expr: str) -> list[list[str]]:
        parts = expr.strip().split()
        if len(parts) != 5:
            raise ValueError(
                f"Invalid cron expression: {expr!r}. "
                f"Expected 5 fields (minute hour day month weekday), got {len(parts)}."
            )
        field_names = ["minute", "hour", "day_of_month", "month", "day_of_week"]
        fields: list[list[str]] = []
        for name, part in zip(field_names, parts):
            parsed = CronTrigger._parse_field(part, name)
            fields.append(parsed)
        return fields

    @staticmethod
    def _parse_field(part: str, name: str) -> list[str]:
        """Parse a single cron field into a list of valid values."""
        ranges = {
            "minute": (0, 59),
            "hour": (0, 23),
            "day_of_month": (1, 31),
            "month": (1, 12),
            "day_of_week": (0, 6),
        }
        if name not in ranges:
            raise ValueError(f"Unknown cron field: {name}")
        lo, hi = ranges[name]

        values: set[int] = set()
        for segment in part.split(","):
            segment = segment.strip()
            if not segment:
                continue

            step = 1
            if "/" in segment:
                segment, step_str = segment.split("/", 1)
                step = int(step_str)

            if segment == "*":
                values.update(range(lo, hi + 1, step))
            elif "-" in segment:
                start_str, end_str = segment.split("-", 1)
                start = int(start_str)
                end = int(end_str)
                values.update(range(start, end + 1, step))
            else:
                values.add(int(segment))

        return [str(v) for v in sorted(values)]

    def get_next_run(self, from_timestamp: float) -> float:
        """Calculate the next datetime this cron expression fires at.

        Uses a simple minute-resolution iteration starting from ``from_timestamp``.
        """
        from datetime import datetime, timedelta, timezone

        dt = datetime.fromtimestamp(from_timestamp, tz=timezone.utc)

        # Start from the next full minute
        dt = dt.replace(second=0, microsecond=0) + timedelta(minutes=1)

        for _ in range(525600):  # search up to 1 year ahead
            minute_vals = self._fields[0]
            hour_vals = self._fields[1]
            day_vals = self._fields[2]
            month_vals = self._fields[3]
            weekday_vals = self._fields[4]

            month_match = str(dt.month) in month_vals
            day_match = str(dt.day) in day_vals
            weekday_match = str(dt.weekday()) in weekday_vals
            hour_match = str(dt.hour) in hour_vals
            minute_match = str(dt.minute) in minute_vals

            # day_of_week OR day_of_month match (standard cron behavior)
            day_valid = day_match or weekday_match

            if month_match and day_valid and hour_match and minute_match:
                return dt.timestamp()

            dt += timedelta(minutes=1)

        raise RuntimeError(
            f"Could not find next run time for cron expression: {self.expr}"
        )


@dataclass
class DateTimeTrigger:
    """Trigger that fires once at a specific datetime.

    Args:
        run_date: ISO-8601 datetime string (e.g. ``"2026-12-25T10:30:00"``).
            If no timezone is specified, UTC is assumed.
    """

    run_date: str

    def __post_init__(self) -> None:
        # Validate on construction
        self.get_run_timestamp()

    def get_run_timestamp(self) -> float:
        """Get the target timestamp for this trigger."""
        from datetime import datetime, timezone

        # Try parsing with various formats
        for fmt in [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]:
            try:
                dt = datetime.strptime(self.run_date, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except ValueError:
                continue

        raise ValueError(
            f"Could not parse datetime: {self.run_date!r}. "
            f"Expected ISO-8601 format (e.g. '2026-12-25T10:30:00')."
        )


@dataclass
class SchedulerConfig:
    """Configuration for the scheduler.

    Attributes:
        timezone: Timezone string (e.g. ``"UTC"``, ``"America/New_York"``).
            If None, UTC is used.
        max_concurrent_jobs: Maximum number of jobs that can run simultaneously.
        log_level: Logging level for scheduler-related logs.
        job_defaults: Default settings applied to every job.
            Supported keys:
                - ``max_instances`` (int): Max concurrent instances of the
                  same job. Default: 3.
                - ``misfire_grace_time`` (int): Seconds after the scheduled
                  fire time that the job will still be accepted. Default: 30.
                - ``coalesce`` (bool): If True, missed firings are merged
                  into one. Default: True.
    """

    timezone: Optional[str] = None
    max_concurrent_jobs: int = 10
    log_level: int = logging.INFO
    job_defaults: Dict[str, Any] = field(
        default_factory=lambda: {
            "max_instances": 3,
            "misfire_grace_time": 30,
            "coalesce": True,
        }
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return {
            "timezone": self.timezone,
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "log_level": self.log_level,
            "job_defaults": self.job_defaults.copy(),
        }


# Default configuration singleton
DEFAULT_CONFIG = SchedulerConfig()

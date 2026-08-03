"""
Configuration module for SOFFEE OpenClaw skill.

Manages cron schedules and broadcast channel configuration for automated
NFL window broadcasts. All settings are configurable via environment variables.
"""

import os
from dataclasses import dataclass


@dataclass
class CronSchedule:
    """Represents a single cron schedule for automated broadcasts."""

    name: str
    description: str
    cron_pattern: str
    time_window: str


class ScheduleConfig:
    """
    Manages OpenClaw cron schedule configuration for automated broadcasts.

    This class loads cron schedules and broadcast channel from environment variables,
    allowing them to be easily customized without code changes. All schedules are
    designed to align with standard NFL broadcast windows (Sunday afternoon/evening
    and Monday/Tuesday morning), as well as proactive roster management checks.

    Environment Variables:
        SOFFEE_BROADCAST_CHANNEL: Slack channel for automated broadcasts
            (default: #nfl-updates)
        SOFFEE_CRON_SUNDAY_10AM: Cron pattern for Sunday 10 AM EST roster sweep
            (default: "0 15 * * 0")
        SOFFEE_CRON_SUNDAY_12PM: Cron pattern for Sunday 12 PM EST
            (default: "0 12 * * 0")
        SOFFEE_CRON_SUNDAY_430PM: Cron pattern for Sunday 4:30 PM EST
            (default: "30 16 * * 0")
        SOFFEE_CRON_SUNDAY_8PM: Cron pattern for Sunday 8 PM EST
            (default: "0 20 * * 0")
        SOFFEE_CRON_MONDAY_TUESDAY_7AM: Cron pattern for Monday/Tuesday 7 AM EST
            (default: "0 12 * * 1,2")
    """

    # Default cron patterns (in UTC, accounting for EST = UTC-5)
    DEFAULT_CRON_SUNDAY_10AM = "0 15 * * 0"  # Sunday 10 AM EST roster sweep
    DEFAULT_CRON_SUNDAY_12PM = "0 17 * * 0"  # Sunday 12 PM EST = 17:00 UTC
    DEFAULT_CRON_SUNDAY_430PM = "30 21 * * 0"  # Sunday 4:30 PM EST = 21:30 UTC
    DEFAULT_CRON_SUNDAY_8PM = "0 1 * * 1"  # Sunday 8 PM EST = 1:00 AM Monday UTC
    DEFAULT_CRON_MONDAY_TUESDAY_7AM = "0 12 * * 1,2"  # Mon/Tue 7 AM EST = 12:00 UTC

    DEFAULT_BROADCAST_CHANNEL = "#nfl-updates"

    def __init__(self):
        """Initialize schedule configuration from environment variables."""
        self.broadcast_channel = os.environ.get(
            "SOFFEE_BROADCAST_CHANNEL", self.DEFAULT_BROADCAST_CHANNEL
        )

        self.schedules = [
            CronSchedule(
                name="sunday_10am_est_roster_sweep",
                description="Sunday 10 AM EST - Automated roster violation sweep",
                cron_pattern=os.environ.get(
                    "SOFFEE_CRON_SUNDAY_10AM", self.DEFAULT_CRON_SUNDAY_10AM
                ),
                time_window="Sunday 10 AM EST",
            ),
            CronSchedule(
                name="sunday_12pm_est",
                description="Sunday 12 PM EST - Early Sunday window",
                cron_pattern=os.environ.get(
                    "SOFFEE_CRON_SUNDAY_12PM", self.DEFAULT_CRON_SUNDAY_12PM
                ),
                time_window="Sunday 12 PM EST",
            ),
            CronSchedule(
                name="sunday_430pm_est",
                description="Sunday 4:30 PM EST - Mid-afternoon Sunday window",
                cron_pattern=os.environ.get(
                    "SOFFEE_CRON_SUNDAY_430PM", self.DEFAULT_CRON_SUNDAY_430PM
                ),
                time_window="Sunday 4:30 PM EST",
            ),
            CronSchedule(
                name="sunday_8pm_est",
                description="Sunday 8 PM EST - Sunday night football",
                cron_pattern=os.environ.get(
                    "SOFFEE_CRON_SUNDAY_8PM", self.DEFAULT_CRON_SUNDAY_8PM
                ),
                time_window="Sunday 8 PM EST",
            ),
            CronSchedule(
                name="monday_tuesday_7am_est",
                description="Monday/Tuesday 7 AM EST - Post-game morning briefing",
                cron_pattern=os.environ.get(
                    "SOFFEE_CRON_MONDAY_TUESDAY_7AM",
                    self.DEFAULT_CRON_MONDAY_TUESDAY_7AM,
                ),
                time_window="Monday/Tuesday 7 AM EST",
            ),
        ]

    def get_schedules(self) -> list[CronSchedule]:
        """
        Get all configured schedules.

        Returns:
            list[CronSchedule]: List of all configured cron schedules.
        """
        return self.schedules

    def get_schedule_by_name(self, name: str) -> CronSchedule | None:
        """
        Get a specific schedule by name.

        Args:
            name: The name of the schedule to retrieve.

        Returns:
            CronSchedule: The requested schedule, or None if not found.
        """
        for schedule in self.schedules:
            if schedule.name == name:
                return schedule
        return None

    def to_openclaw_metadata(self) -> dict:
        """
        Convert schedule configuration to OpenClaw skill metadata format.

        Returns:
            dict: OpenClaw metadata structure with schedules and channel info.
        """
        return {
            "schedules": [
                {
                    "name": schedule.name,
                    "description": schedule.description,
                    "cron": schedule.cron_pattern,
                    "channel": self.broadcast_channel,
                }
                for schedule in self.schedules
            ],
            "broadcast_channel": self.broadcast_channel,
        }

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate schedule configuration.

        Checks that:
        - All cron patterns are valid format (basic validation)
        - Broadcast channel is not empty
        - Channel name follows Slack naming conventions if specified

        Returns:
            tuple[bool, list[str]]: A tuple of (is_valid, error_messages).
        """
        errors = []

        # Validate broadcast channel
        if not self.broadcast_channel:
            errors.append("Broadcast channel is empty")
        elif not self.broadcast_channel.startswith(
            "#"
        ) and not self.broadcast_channel.startswith("C"):
            errors.append(
                f"Invalid channel format: {self.broadcast_channel}. "
                "Must start with # for channel names or C for channel IDs."
            )

        # Validate each schedule's cron pattern (basic format check)
        for schedule in self.schedules:
            if not self._is_valid_cron(schedule.cron_pattern):
                errors.append(
                    f"Invalid cron pattern for {schedule.name}: {schedule.cron_pattern}"
                )

        return len(errors) == 0, errors

    @staticmethod
    def _is_valid_cron(pattern: str) -> bool:
        """
        Perform basic validation of cron pattern format.

        A valid cron pattern has 5 or 6 space-separated fields:
        minute hour day month day-of-week [year]

        Args:
            pattern: The cron pattern to validate.

        Returns:
            bool: True if pattern appears to be valid, False otherwise.
        """
        if not isinstance(pattern, str):
            return False

        parts = pattern.split()
        if len(parts) not in (5, 6):
            return False

        # Basic check: each part should not be empty and should contain
        # valid cron characters (numbers, *, /, -, ,)
        valid_chars = set("0123456789*/-,")
        for part in parts:
            if not part or not all(c in valid_chars for c in part):
                return False

        return True


def get_schedule_config() -> ScheduleConfig:
    """
    Get the global schedule configuration instance.

    Returns:
        ScheduleConfig: The initialized schedule configuration.
    """
    return ScheduleConfig()

"""Tests for the configuration module."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add the root directory to the path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CronSchedule, ScheduleConfig


class TestCronSchedule:
    """Test suite for CronSchedule dataclass."""

    def test_cron_schedule_creation(self):
        """Test that CronSchedule can be created with all fields."""
        schedule = CronSchedule(
            name="test_schedule",
            description="Test schedule",
            cron_pattern="0 12 * * 0",
            time_window="Sunday 12 PM",
        )
        assert schedule.name == "test_schedule"
        assert schedule.description == "Test schedule"
        assert schedule.cron_pattern == "0 12 * * 0"
        assert schedule.time_window == "Sunday 12 PM"

    def test_cron_schedule_dataclass_fields(self):
        """Test that CronSchedule has expected fields."""
        schedule = CronSchedule(
            name="test",
            description="desc",
            cron_pattern="0 * * * *",
            time_window="hourly",
        )
        assert hasattr(schedule, "name")
        assert hasattr(schedule, "description")
        assert hasattr(schedule, "cron_pattern")
        assert hasattr(schedule, "time_window")


class TestScheduleConfigInitialization:
    """Test suite for ScheduleConfig initialization."""

    def test_schedule_config_initialization_defaults(self):
        """Test that ScheduleConfig initializes with default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = ScheduleConfig()
            assert config.broadcast_channel == "#nfl-updates"
            assert len(config.schedules) == 5

    def test_schedule_config_initialization_custom_channel(self):
        """Test that ScheduleConfig respects custom channel environment variable."""
        env_vars = {
            "SOFFEE_BROADCAST_CHANNEL": "#fantasy-league",
        }
        with patch.dict(os.environ, env_vars):
            config = ScheduleConfig()
            assert config.broadcast_channel == "#fantasy-league"

    def test_schedule_config_initialization_custom_cron_patterns(self):
        """Test custom cron pattern environment variables."""
        env_vars = {
            "SOFFEE_CRON_SUNDAY_12PM": "0 8 * * 0",
            "SOFFEE_CRON_SUNDAY_430PM": "30 12 * * 0",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = ScheduleConfig()
            sunday_12pm = config.get_schedule_by_name("sunday_12pm_est")
            sunday_430pm = config.get_schedule_by_name("sunday_430pm_est")
            assert sunday_12pm.cron_pattern == "0 8 * * 0"
            assert sunday_430pm.cron_pattern == "30 12 * * 0"

    def test_schedule_config_has_five_schedules(self):
        """Test that ScheduleConfig creates exactly five schedules."""
        with patch.dict(os.environ, {}, clear=True):
            config = ScheduleConfig()
            assert len(config.schedules) == 5

    def test_schedule_config_schedule_names(self):
        """Test that all expected schedules are present by name."""
        with patch.dict(os.environ, {}, clear=True):
            config = ScheduleConfig()
            names = {schedule.name for schedule in config.schedules}
            expected_names = {
                "sunday_10am_est_roster_sweep",
                "sunday_12pm_est",
                "sunday_430pm_est",
                "sunday_8pm_est",
                "monday_tuesday_7am_est",
            }
            assert names == expected_names


class TestGetSchedules:
    """Test suite for get_schedules method."""

    def test_get_schedules_returns_list(self):
        """Test that get_schedules returns a list."""
        with patch.dict(os.environ, {}, clear=True):
            config = ScheduleConfig()
            schedules = config.get_schedules()
            assert isinstance(schedules, list)

    def test_get_schedules_returns_all_schedules(self):
        """Test that get_schedules returns all configured schedules."""
        with patch.dict(os.environ, {}, clear=True):
            config = ScheduleConfig()
            schedules = config.get_schedules()
            assert len(config.schedules) == 5
            assert all(isinstance(s, CronSchedule) for s in schedules)

    def test_get_schedules_returns_cron_schedule_objects(self):
        """Test that each schedule is a CronSchedule object."""
        with patch.dict(os.environ, {}, clear=True):
            config = ScheduleConfig()
            schedules = config.get_schedules()
            for schedule in schedules:
                assert isinstance(schedule, CronSchedule)
                assert hasattr(schedule, "name")
                assert hasattr(schedule, "cron_pattern")


class TestGetScheduleByName:
    """Test suite for get_schedule_by_name method."""

    def test_get_schedule_by_name_existing_schedule(self):
        """Test retrieving an existing schedule by name."""
        with patch.dict(os.environ, {}, clear=True):
            config = ScheduleConfig()
            schedule = config.get_schedule_by_name("sunday_12pm_est")
            assert schedule is not None
            assert schedule.name == "sunday_12pm_est"
            assert "12 PM" in schedule.description or "12:00" in schedule.cron_pattern

    def test_get_schedule_by_name_nonexistent_schedule(self):
        """Test that get_schedule_by_name returns None for non-existent schedule."""
        with patch.dict(os.environ, {}, clear=True):
            config = ScheduleConfig()
            schedule = config.get_schedule_by_name("nonexistent_schedule")
            assert schedule is None

    def test_get_schedule_by_name_all_schedules(self):
        """Test retrieving each of the four default schedules by name."""
        with patch.dict(os.environ, {}, clear=True):
            config = ScheduleConfig()
            expected_names = [
                "sunday_12pm_est",
                "sunday_430pm_est",
                "sunday_8pm_est",
                "monday_tuesday_7am_est",
            ]
            for name in expected_names:
                schedule = config.get_schedule_by_name(name)
                assert schedule is not None
                assert schedule.name == name


class TestToOpenclawMetadata:
    """Test suite for to_openclaw_metadata method."""

    def test_to_openclaw_metadata_returns_dict(self):
        """Test that to_openclaw_metadata returns a dictionary."""
        with patch.dict(os.environ, {}, clear=True):
            config = ScheduleConfig()
            metadata = config.to_openclaw_metadata()
            assert isinstance(metadata, dict)

    def test_to_openclaw_metadata_has_schedules_key(self):
        """Test that metadata includes 'schedules' key."""
        with patch.dict(os.environ, {}, clear=True):
            config = ScheduleConfig()
            metadata = config.to_openclaw_metadata()
            assert "schedules" in metadata

    def test_to_openclaw_metadata_has_broadcast_channel_key(self):
        """Test that metadata includes 'broadcast_channel' key."""
        with patch.dict(os.environ, {}, clear=True):
            config = ScheduleConfig()
            metadata = config.to_openclaw_metadata()
            assert "broadcast_channel" in metadata

    def test_to_openclaw_metadata_schedules_count(self):
        """Test that metadata contains all four schedules."""
        with patch.dict(os.environ, {}, clear=True):
            config = ScheduleConfig()
            config.to_openclaw_metadata()
            assert len(config.schedules) == 5

    def test_to_openclaw_metadata_schedule_structure(self):
        """Test that each schedule in metadata has required fields."""
        with patch.dict(os.environ, {}, clear=True):
            config = ScheduleConfig()
            metadata = config.to_openclaw_metadata()
            for schedule in metadata["schedules"]:
                assert "name" in schedule
                assert "description" in schedule
                assert "cron" in schedule
                assert "channel" in schedule

    def test_to_openclaw_metadata_channel_value(self):
        """Test that metadata broadcasts include correct channel."""
        with patch.dict(os.environ, {"SOFFEE_BROADCAST_CHANNEL": "#test-channel"}):
            config = ScheduleConfig()
            metadata = config.to_openclaw_metadata()
            for schedule in metadata["schedules"]:
                assert schedule["channel"] == "#test-channel"


class TestValidate:
    """Test suite for validate method."""

    def test_validate_returns_tuple(self):
        """Test that validate returns a tuple."""
        with patch.dict(os.environ, {}, clear=True):
            config = ScheduleConfig()
            result = config.validate()
            assert isinstance(result, tuple)
            assert len(result) == 2

    def test_validate_valid_config(self):
        """Test that valid configuration passes validation."""
        with patch.dict(os.environ, {}, clear=True):
            config = ScheduleConfig()
            is_valid, errors = config.validate()
            assert is_valid is True
            assert len(errors) == 0

    def test_validate_empty_channel(self):
        """Test that empty channel fails validation."""
        with patch.dict(os.environ, {"SOFFEE_BROADCAST_CHANNEL": ""}):
            config = ScheduleConfig()
            is_valid, errors = config.validate()
            assert is_valid is False
            assert len(errors) > 0

    def test_validate_invalid_channel_format(self):
        """Test that invalid channel format fails validation."""
        with patch.dict(os.environ, {"SOFFEE_BROADCAST_CHANNEL": "invalid-channel"}):
            config = ScheduleConfig()
            is_valid, errors = config.validate()
            assert is_valid is False
            assert any("channel format" in error.lower() for error in errors)

    def test_validate_valid_channel_with_hash(self):
        """Test that channel with # passes validation."""
        with patch.dict(os.environ, {"SOFFEE_BROADCAST_CHANNEL": "#valid-channel"}):
            config = ScheduleConfig()
            is_valid, errors = config.validate()
            assert is_valid is True

    def test_validate_valid_channel_id_format(self):
        """Test that channel ID format (starting with C) passes validation."""
        with patch.dict(os.environ, {"SOFFEE_BROADCAST_CHANNEL": "C1234567890"}):
            config = ScheduleConfig()
            is_valid, errors = config.validate()
            assert is_valid is True

    def test_validate_invalid_cron_pattern_too_few_fields(self):
        """Test that cron pattern with too few fields fails validation."""
        with patch.dict(os.environ, {"SOFFEE_CRON_SUNDAY_12PM": "0 12 *"}):
            config = ScheduleConfig()
            is_valid, errors = config.validate()
            assert is_valid is False
            assert any("cron" in error.lower() for error in errors)

    def test_validate_invalid_cron_pattern_invalid_characters(self):
        """Test that cron pattern with invalid characters fails validation."""
        with patch.dict(os.environ, {"SOFFEE_CRON_SUNDAY_12PM": "0 12 * * ? invalid"}):
            config = ScheduleConfig()
            is_valid, errors = config.validate()
            assert is_valid is False
            assert any("cron" in error.lower() for error in errors)

    def test_validate_valid_cron_pattern_with_list(self):
        """Test that cron pattern with comma-separated values passes validation."""
        with patch.dict(os.environ, {"SOFFEE_CRON_MONDAY_TUESDAY_7AM": "0 7 * * 1,2"}):
            config = ScheduleConfig()
            is_valid, errors = config.validate()
            assert is_valid is True

    def test_validate_valid_cron_pattern_with_range(self):
        """Test that cron pattern with range passes validation."""
        with patch.dict(os.environ, {"SOFFEE_CRON_SUNDAY_12PM": "0 12-18 * * 0"}):
            config = ScheduleConfig()
            is_valid, errors = config.validate()
            assert is_valid is True


class TestIsValidCron:
    """Test suite for _is_valid_cron static method."""

    def test_is_valid_cron_valid_pattern(self):
        """Test that valid 5-field cron pattern passes."""
        assert ScheduleConfig._is_valid_cron("0 12 * * 0") is True

    def test_is_valid_cron_valid_6_field_pattern(self):
        """Test that valid 6-field cron pattern passes."""
        assert ScheduleConfig._is_valid_cron("0 12 * * 0 2024") is True

    def test_is_valid_cron_invalid_too_few_fields(self):
        """Test that cron pattern with too few fields fails."""
        assert ScheduleConfig._is_valid_cron("0 12 *") is False

    def test_is_valid_cron_invalid_too_many_fields(self):
        """Test that cron pattern with too many fields fails."""
        assert ScheduleConfig._is_valid_cron("0 12 * * 0 2024 extra") is False

    def test_is_valid_cron_invalid_characters(self):
        """Test that cron pattern with invalid characters fails."""
        assert ScheduleConfig._is_valid_cron("0 12 * * ? extra") is False

    def test_is_valid_cron_empty_string(self):
        """Test that empty string fails."""
        assert ScheduleConfig._is_valid_cron("") is False

    def test_is_valid_cron_non_string_input(self):
        """Test that non-string input fails."""
        assert ScheduleConfig._is_valid_cron(None) is False
        assert ScheduleConfig._is_valid_cron(123) is False
        assert ScheduleConfig._is_valid_cron([]) is False

    def test_is_valid_cron_with_wildcards(self):
        """Test that patterns with wildcards pass."""
        assert ScheduleConfig._is_valid_cron("* * * * *") is True

    def test_is_valid_cron_with_ranges(self):
        """Test that patterns with ranges pass."""
        assert ScheduleConfig._is_valid_cron("0 12-18 * * 0") is True
        assert ScheduleConfig._is_valid_cron("0-30 12 * * 0") is True

    def test_is_valid_cron_with_lists(self):
        """Test that patterns with comma-separated values pass."""
        assert ScheduleConfig._is_valid_cron("0 12 * * 0,1,2") is True
        assert ScheduleConfig._is_valid_cron("0,30 12 * * 0") is True

    def test_is_valid_cron_with_step_values(self):
        """Test that patterns with step values pass."""
        assert ScheduleConfig._is_valid_cron("*/5 12 * * 0") is True
        assert ScheduleConfig._is_valid_cron("0 */2 * * 0") is True


class TestDefaultConstants:
    """Test suite for default constant values."""

    def test_default_channel_value(self):
        """Test that default broadcast channel is set."""
        assert ScheduleConfig.DEFAULT_BROADCAST_CHANNEL == "#nfl-updates"

    def test_default_cron_values_are_strings(self):
        """Test that all default cron values are strings."""
        assert isinstance(ScheduleConfig.DEFAULT_CRON_SUNDAY_10AM, str)
        assert isinstance(ScheduleConfig.DEFAULT_CRON_SUNDAY_12PM, str)
        assert isinstance(ScheduleConfig.DEFAULT_CRON_SUNDAY_430PM, str)
        assert isinstance(ScheduleConfig.DEFAULT_CRON_SUNDAY_8PM, str)
        assert isinstance(ScheduleConfig.DEFAULT_CRON_MONDAY_TUESDAY_7AM, str)

    def test_default_cron_values_are_valid(self):
        """Test that all default cron values are valid patterns."""
        assert ScheduleConfig._is_valid_cron(ScheduleConfig.DEFAULT_CRON_SUNDAY_10AM)
        assert ScheduleConfig._is_valid_cron(ScheduleConfig.DEFAULT_CRON_SUNDAY_12PM)
        assert ScheduleConfig._is_valid_cron(ScheduleConfig.DEFAULT_CRON_SUNDAY_430PM)
        assert ScheduleConfig._is_valid_cron(ScheduleConfig.DEFAULT_CRON_SUNDAY_8PM)
        assert ScheduleConfig._is_valid_cron(
            ScheduleConfig.DEFAULT_CRON_MONDAY_TUESDAY_7AM
        )

    def test_default_monday_tuesday_cron_targets_monday_and_tuesday(self):
        """Test that the Monday/Tuesday schedule fires on the intended days."""
        assert ScheduleConfig.DEFAULT_CRON_MONDAY_TUESDAY_7AM == "0 12 * * 1,2"

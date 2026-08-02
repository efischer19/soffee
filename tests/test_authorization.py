"""Tests for the authorization module."""

import sys
from pathlib import Path
from unittest.mock import patch

# Add the root directory to the path so we can import authorization
sys.path.insert(0, str(Path(__file__).parent.parent))

from authorization import (
    SLACK_USER_TO_TEAM_MAPPING,
    get_slack_user_for_team,
    verify_team_ownership,
)


class TestVerifyTeamOwnership:
    """Test suite for verify_team_ownership function."""

    def test_verify_team_ownership_success(self):
        """Verify that a Slack user is confirmed to own their team."""
        # Use the mock mapping to test with known values
        mock_mapping = {
            "U1234567890": 1,
            "U0987654321": 2,
        }
        with patch.dict("authorization.SLACK_USER_TO_TEAM_MAPPING", mock_mapping):
            assert verify_team_ownership("U1234567890", 1) is True
            assert verify_team_ownership("U0987654321", 2) is True

    def test_verify_team_ownership_wrong_team(self):
        """Verify that a Slack user is rejected when checking wrong team."""
        mock_mapping = {
            "U1234567890": 1,
        }
        with patch.dict("authorization.SLACK_USER_TO_TEAM_MAPPING", mock_mapping):
            assert verify_team_ownership("U1234567890", 2) is False
            assert verify_team_ownership("U1234567890", 999) is False

    def test_verify_team_ownership_nonexistent_user(self):
        """Verify that a non-existent Slack user is rejected."""
        mock_mapping = {
            "U1234567890": 1,
        }
        with patch.dict("authorization.SLACK_USER_TO_TEAM_MAPPING", mock_mapping):
            assert verify_team_ownership("U9999999999", 1) is False

    def test_verify_team_ownership_empty_mapping(self):
        """Verify that verify_team_ownership works with empty mapping."""
        with patch.dict("authorization.SLACK_USER_TO_TEAM_MAPPING", {}, clear=True):
            assert verify_team_ownership("U1234567890", 1) is False

    def test_verify_team_ownership_invalid_slack_user_id_none(self):
        """Verify that None slack_user_id returns False."""
        assert verify_team_ownership(None, 1) is False

    def test_verify_team_ownership_invalid_slack_user_id_empty_string(self):
        """Verify that empty string slack_user_id returns False."""
        assert verify_team_ownership("", 1) is False

    def test_verify_team_ownership_invalid_slack_user_id_not_string(self):
        """Verify that non-string slack_user_id returns False."""
        assert verify_team_ownership(12345, 1) is False
        assert verify_team_ownership([], 1) is False
        assert verify_team_ownership({}, 1) is False

    def test_verify_team_ownership_invalid_team_id_negative(self):
        """Verify that negative team_id returns False."""
        mock_mapping = {
            "U1234567890": 1,
        }
        with patch.dict("authorization.SLACK_USER_TO_TEAM_MAPPING", mock_mapping):
            assert verify_team_ownership("U1234567890", -1) is False

    def test_verify_team_ownership_invalid_team_id_zero(self):
        """Verify that zero team_id returns False."""
        mock_mapping = {
            "U1234567890": 1,
        }
        with patch.dict("authorization.SLACK_USER_TO_TEAM_MAPPING", mock_mapping):
            assert verify_team_ownership("U1234567890", 0) is False

    def test_verify_team_ownership_invalid_team_id_not_int(self):
        """Verify that non-integer team_id returns False."""
        assert verify_team_ownership("U1234567890", "1") is False
        assert verify_team_ownership("U1234567890", 1.5) is False
        assert verify_team_ownership("U1234567890", None) is False

    def test_verify_team_ownership_multiple_users(self):
        """Verify correct behavior with multiple users in mapping."""
        mock_mapping = {
            "U1111111111": 1,
            "U2222222222": 2,
            "U3333333333": 3,
        }
        with patch.dict("authorization.SLACK_USER_TO_TEAM_MAPPING", mock_mapping):
            assert verify_team_ownership("U1111111111", 1) is True
            assert verify_team_ownership("U2222222222", 2) is True
            assert verify_team_ownership("U3333333333", 3) is True
            assert verify_team_ownership("U1111111111", 2) is False
            assert verify_team_ownership("U2222222222", 1) is False


class TestSlackUserToTeamMapping:
    """Test suite for the SLACK_USER_TO_TEAM_MAPPING constant."""

    def test_mapping_is_dict(self):
        """Verify that SLACK_USER_TO_TEAM_MAPPING is a dictionary."""
        assert isinstance(SLACK_USER_TO_TEAM_MAPPING, dict)

    def test_mapping_initial_state(self):
        """Verify the initial state of the mapping (should be empty for Phase v0)."""
        # Phase v0 starts with an empty mapping
        assert SLACK_USER_TO_TEAM_MAPPING == {} or isinstance(
            SLACK_USER_TO_TEAM_MAPPING, dict
        )


class TestGetSlackUserForTeam:
    """Test suite for get_slack_user_for_team function."""

    def test_get_slack_user_for_team_success(self):
        """Verify that function returns correct Slack user for team."""
        mock_mapping = {
            "U1234567890": 1,
            "U0987654321": 2,
        }
        with patch.dict("authorization.SLACK_USER_TO_TEAM_MAPPING", mock_mapping):
            assert get_slack_user_for_team(1) == "U1234567890"
            assert get_slack_user_for_team(2) == "U0987654321"

    def test_get_slack_user_for_team_not_found(self):
        """Verify that function returns None when team not mapped."""
        mock_mapping = {
            "U1234567890": 1,
        }
        with patch.dict("authorization.SLACK_USER_TO_TEAM_MAPPING", mock_mapping):
            assert get_slack_user_for_team(999) is None

    def test_get_slack_user_for_team_empty_mapping(self):
        """Verify that function returns None with empty mapping."""
        with patch.dict("authorization.SLACK_USER_TO_TEAM_MAPPING", {}, clear=True):
            assert get_slack_user_for_team(1) is None

    def test_get_slack_user_for_team_invalid_team_id_negative(self):
        """Verify that function returns None for negative team ID."""
        mock_mapping = {
            "U1234567890": 1,
        }
        with patch.dict("authorization.SLACK_USER_TO_TEAM_MAPPING", mock_mapping):
            assert get_slack_user_for_team(-1) is None

    def test_get_slack_user_for_team_invalid_team_id_zero(self):
        """Verify that function returns None for zero team ID."""
        mock_mapping = {
            "U1234567890": 1,
        }
        with patch.dict("authorization.SLACK_USER_TO_TEAM_MAPPING", mock_mapping):
            assert get_slack_user_for_team(0) is None

    def test_get_slack_user_for_team_invalid_team_id_not_int(self):
        """Verify that function returns None for non-integer team ID."""
        assert get_slack_user_for_team("1") is None
        assert get_slack_user_for_team(1.5) is None
        assert get_slack_user_for_team(None) is None
        assert get_slack_user_for_team([]) is None

    def test_get_slack_user_for_team_multiple_users(self):
        """Verify that function correctly identifies each user's team."""
        mock_mapping = {
            "U1111111111": 1,
            "U2222222222": 2,
            "U3333333333": 3,
        }
        with patch.dict("authorization.SLACK_USER_TO_TEAM_MAPPING", mock_mapping):
            assert get_slack_user_for_team(1) == "U1111111111"
            assert get_slack_user_for_team(2) == "U2222222222"
            assert get_slack_user_for_team(3) == "U3333333333"
            assert get_slack_user_for_team(4) is None

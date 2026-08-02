"""Tests for the main SOFFEE module."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the root directory to the path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import initialize_league


def test_initialize_league_success():
    """Verify that initialize_league returns a League object with valid credentials."""
    env_vars = {
        "ESPN_SWID": "test_swid",
        "ESPN_S2": "test_s2",
        "ESPN_LEAGUE_ID": "12345",
        "ESPN_YEAR": "2024",
    }

    with (
        patch.dict(os.environ, env_vars, clear=False),
        patch("main.League") as mock_league,
    ):
        mock_instance = MagicMock()
        mock_league.return_value = mock_instance

        result = initialize_league()

        assert result is mock_instance
        mock_league.assert_called_once_with(
            league_id=12345, year=2024, espn_s2="test_s2", swid="test_swid"
        )


def test_initialize_league_missing_swid(capsys):
    """Verify that initialize_league returns None when ESPN_SWID is missing."""
    env_vars = {
        "ESPN_S2": "test_s2",
        "ESPN_LEAGUE_ID": "12345",
        "ESPN_YEAR": "2024",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        result = initialize_league()
        captured = capsys.readouterr()

        assert result is None
        assert "ESPN_SWID" in captured.out
        assert "Missing ESPN credentials" in captured.out


def test_initialize_league_missing_s2(capsys):
    """Verify that initialize_league returns None when ESPN_S2 is missing."""
    env_vars = {
        "ESPN_SWID": "test_swid",
        "ESPN_LEAGUE_ID": "12345",
        "ESPN_YEAR": "2024",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        result = initialize_league()
        captured = capsys.readouterr()

        assert result is None
        assert "ESPN_S2" in captured.out
        assert "Missing ESPN credentials" in captured.out


def test_initialize_league_missing_league_id(capsys):
    """Verify that initialize_league returns None when ESPN_LEAGUE_ID is missing."""
    env_vars = {
        "ESPN_SWID": "test_swid",
        "ESPN_S2": "test_s2",
        "ESPN_YEAR": "2024",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        result = initialize_league()
        captured = capsys.readouterr()

        assert result is None
        assert "ESPN_LEAGUE_ID" in captured.out
        assert "Missing ESPN credentials" in captured.out


def test_initialize_league_missing_year(capsys):
    """Verify that initialize_league returns None when ESPN_YEAR is missing."""
    env_vars = {
        "ESPN_SWID": "test_swid",
        "ESPN_S2": "test_s2",
        "ESPN_LEAGUE_ID": "12345",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        result = initialize_league()
        captured = capsys.readouterr()

        assert result is None
        assert "ESPN_YEAR" in captured.out
        assert "Missing ESPN credentials" in captured.out


def test_initialize_league_invalid_league_id(capsys):
    """Verify that initialize_league handles invalid league_id gracefully."""
    env_vars = {
        "ESPN_SWID": "test_swid",
        "ESPN_S2": "test_s2",
        "ESPN_LEAGUE_ID": "not_a_number",
        "ESPN_YEAR": "2024",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        result = initialize_league()
        captured = capsys.readouterr()

        assert result is None
        assert "Invalid ESPN credentials format" in captured.out


def test_initialize_league_invalid_year(capsys):
    """Verify that initialize_league handles invalid year gracefully."""
    env_vars = {
        "ESPN_SWID": "test_swid",
        "ESPN_S2": "test_s2",
        "ESPN_LEAGUE_ID": "12345",
        "ESPN_YEAR": "not_a_year",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        result = initialize_league()
        captured = capsys.readouterr()

        assert result is None
        assert "Invalid ESPN credentials format" in captured.out


def test_initialize_league_api_error(capsys):
    """Verify that initialize_league handles API errors gracefully."""
    env_vars = {
        "ESPN_SWID": "test_swid",
        "ESPN_S2": "test_s2",
        "ESPN_LEAGUE_ID": "12345",
        "ESPN_YEAR": "2024",
    }

    with (
        patch.dict(os.environ, env_vars, clear=False),
        patch("main.League") as mock_league,
    ):
        mock_league.side_effect = Exception("API error")

        result = initialize_league()
        captured = capsys.readouterr()

        assert result is None
        assert "Failed to initialize ESPN League" in captured.out

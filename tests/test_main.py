"""Tests for the main SOFFEE module."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the root directory to the path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import get_current_matchups, initialize_league


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


def test_get_current_matchups_with_none_league():
    """Verify that get_current_matchups returns error when league is None."""
    result = get_current_matchups(None)

    assert result["success"] is False
    assert "League is None" in result["error"]


def test_get_current_matchups_success():
    """Verify that get_current_matchups returns formatted matchup data."""
    # Create mock league and box scores
    mock_league = MagicMock()
    mock_league.current_week = 5

    # Create mock home and away teams
    mock_home_team = MagicMock()
    mock_home_team.team_name = "Team A"

    mock_away_team = MagicMock()
    mock_away_team.team_name = "Team B"

    # Create mock box score
    mock_box_score = MagicMock()
    mock_box_score.home_team = mock_home_team
    mock_box_score.away_team = mock_away_team
    mock_box_score.home_score = 125.50
    mock_box_score.away_score = 118.25
    mock_box_score.home_projected = 135.75
    mock_box_score.away_projected = 130.00

    mock_league.box_scores.return_value = [mock_box_score]

    result = get_current_matchups(mock_league)

    assert result["success"] is True
    assert result["week"] == 5
    assert len(result["matchups"]) == 1

    matchup = result["matchups"][0]
    assert matchup["home_team"] == "Team A"
    assert matchup["away_team"] == "Team B"
    assert matchup["home_score"] == 125.50
    assert matchup["away_score"] == 118.25
    assert matchup["home_projected"] == 135.75
    assert matchup["away_projected"] == 130.00
    assert matchup["matchup_id"] == 0


def test_get_current_matchups_multiple_matchups():
    """Verify that get_current_matchups handles multiple matchups."""
    mock_league = MagicMock()
    mock_league.current_week = 3

    # Create two matchups
    matchup_data = [
        {
            "home": "Team A",
            "away": "Team B",
            "h_score": 100.0,
            "a_score": 95.5,
            "h_proj": 110.0,
            "a_proj": 105.0,
        },
        {
            "home": "Team C",
            "away": "Team D",
            "h_score": 120.0,
            "a_score": 115.5,
            "h_proj": 130.0,
            "a_proj": 125.0,
        },
    ]

    box_scores = []
    for data in matchup_data:
        home_team = MagicMock()
        home_team.team_name = data["home"]
        away_team = MagicMock()
        away_team.team_name = data["away"]

        box_score = MagicMock()
        box_score.home_team = home_team
        box_score.away_team = away_team
        box_score.home_score = data["h_score"]
        box_score.away_score = data["a_score"]
        box_score.home_projected = data["h_proj"]
        box_score.away_projected = data["a_proj"]

        box_scores.append(box_score)

    mock_league.box_scores.return_value = box_scores

    result = get_current_matchups(mock_league)

    assert result["success"] is True
    assert result["week"] == 3
    assert len(result["matchups"]) == 2

    # Verify first matchup
    assert result["matchups"][0]["home_team"] == "Team A"
    assert result["matchups"][0]["matchup_id"] == 0

    # Verify second matchup
    assert result["matchups"][1]["home_team"] == "Team C"
    assert result["matchups"][1]["matchup_id"] == 1


def test_get_current_matchups_no_matchups():
    """Verify that get_current_matchups returns empty matchups when none exist."""
    mock_league = MagicMock()
    mock_league.current_week = 10
    mock_league.box_scores.return_value = []

    result = get_current_matchups(mock_league)

    assert result["success"] is True
    assert result["week"] == 10
    assert result["matchups"] == []


def test_get_current_matchups_current_week_none():
    """Verify that get_current_matchups returns error when current_week is None."""
    mock_league = MagicMock()
    mock_league.current_week = None

    result = get_current_matchups(mock_league)

    assert result["success"] is False
    assert "Unable to determine current week" in result["error"]


def test_get_current_matchups_attribute_error():
    """Verify that get_current_matchups handles attribute errors gracefully."""
    mock_league = MagicMock()
    mock_league.current_week = 5
    # Simulate a missing attribute error
    mock_league.box_scores.side_effect = AttributeError("Missing attribute")

    result = get_current_matchups(mock_league)

    assert result["success"] is False
    assert "Invalid league data structure" in result["error"]


def test_get_current_matchups_connection_error():
    """Verify that get_current_matchups handles connection errors gracefully."""
    mock_league = MagicMock()
    mock_league.current_week = 5
    mock_league.box_scores.side_effect = ConnectionError("Connection failed")

    result = get_current_matchups(mock_league)

    assert result["success"] is False
    assert "API connection error" in result["error"]


def test_get_current_matchups_timeout_error():
    """Verify that get_current_matchups handles timeout errors gracefully."""
    mock_league = MagicMock()
    mock_league.current_week = 5
    mock_league.box_scores.side_effect = TimeoutError("Request timeout")

    result = get_current_matchups(mock_league)

    assert result["success"] is False
    assert "API connection error" in result["error"]


def test_get_current_matchups_generic_exception():
    """Verify that get_current_matchups handles generic exceptions gracefully."""
    mock_league = MagicMock()
    mock_league.current_week = 5
    mock_league.box_scores.side_effect = ValueError("Unexpected error")

    result = get_current_matchups(mock_league)

    assert result["success"] is False
    assert "Unexpected error fetching matchups" in result["error"]


def test_get_current_matchups_score_rounding():
    """Verify that scores are properly rounded to 2 decimal places."""
    mock_league = MagicMock()
    mock_league.current_week = 2

    mock_home_team = MagicMock()
    mock_home_team.team_name = "Team A"
    mock_away_team = MagicMock()
    mock_away_team.team_name = "Team B"

    mock_box_score = MagicMock()
    mock_box_score.home_team = mock_home_team
    mock_box_score.away_team = mock_away_team
    # Use values that require rounding
    mock_box_score.home_score = 125.5555
    mock_box_score.away_score = 118.2588
    mock_box_score.home_projected = 135.7512
    mock_box_score.away_projected = 130.0049

    mock_league.box_scores.return_value = [mock_box_score]

    result = get_current_matchups(mock_league)

    matchup = result["matchups"][0]
    assert matchup["home_score"] == 125.56
    assert matchup["away_score"] == 118.26
    assert matchup["home_projected"] == 135.75
    assert matchup["away_projected"] == 130.00

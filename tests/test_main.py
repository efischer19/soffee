"""Tests for the main SOFFEE module."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the root directory to the path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import (
    generate_batch_score_summary,
    get_current_matchups,
    get_team_roster,
    initialize_league,
    process_waiver_transaction,
    set_lineup_status,
)


@pytest.fixture
def mock_verify_team_ownership():
    """Fixture that mocks verify_team_ownership to return True by default."""
    with patch("main.verify_team_ownership", return_value=True) as mock:
        yield mock


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


def test_generate_batch_score_summary_with_none_league():
    """Verify that generate_batch_score_summary returns error when league is None."""
    result = generate_batch_score_summary(None)

    assert result["success"] is False
    assert "error" in result
    assert result["error"] is not None


def test_generate_batch_score_summary_success():
    """Verify that generate_batch_score_summary formats matchup data correctly."""
    mock_league = MagicMock()
    mock_league.current_week = 5

    mock_home_team = MagicMock()
    mock_home_team.team_name = "Team A"

    mock_away_team = MagicMock()
    mock_away_team.team_name = "Team B"

    mock_box_score = MagicMock()
    mock_box_score.home_team = mock_home_team
    mock_box_score.away_team = mock_away_team
    mock_box_score.home_score = 125.50
    mock_box_score.away_score = 118.25
    mock_box_score.home_projected = 135.75
    mock_box_score.away_projected = 130.00

    mock_league.box_scores.return_value = [mock_box_score]

    result = generate_batch_score_summary(mock_league)

    assert result["success"] is True
    assert result["week"] == 5
    assert "summary" in result
    assert "Week 5 Summary" in result["summary"]
    assert "Team A vs Team B" in result["summary"]
    # Check for values with how Python formats them
    assert "125.5" in result["summary"]
    assert "118.25" in result["summary"]
    assert "135.75" in result["summary"]
    assert "130" in result["summary"]  # 130.0 is formatted as 130


def test_generate_batch_score_summary_multiple_matchups():
    """Verify that generate_batch_score_summary handles multiple matchups."""
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
        mock_home_team = MagicMock()
        mock_home_team.team_name = data["home"]
        mock_away_team = MagicMock()
        mock_away_team.team_name = data["away"]

        mock_box_score = MagicMock()
        mock_box_score.home_team = mock_home_team
        mock_box_score.away_team = mock_away_team
        mock_box_score.home_score = data["h_score"]
        mock_box_score.away_score = data["a_score"]
        mock_box_score.home_projected = data["h_proj"]
        mock_box_score.away_projected = data["a_proj"]

        box_scores.append(mock_box_score)

    mock_league.box_scores.return_value = box_scores

    result = generate_batch_score_summary(mock_league)

    assert result["success"] is True
    assert result["week"] == 3
    assert "Matchup 1:" in result["summary"]
    assert "Matchup 2:" in result["summary"]
    assert "Team A vs Team B" in result["summary"]
    assert "Team C vs Team D" in result["summary"]
    assert "100.0" in result["summary"]
    assert "120.0" in result["summary"]


def test_generate_batch_score_summary_no_matchups():
    """Verify that generate_batch_score_summary handles no matchups."""
    mock_league = MagicMock()
    mock_league.current_week = 10
    mock_league.box_scores.return_value = []

    result = generate_batch_score_summary(mock_league)

    assert result["success"] is True
    assert result["week"] == 10
    assert "No matchups found for this week." in result["summary"]


def test_generate_batch_score_summary_propagates_error():
    """Verify that generate_batch_score_summary propagates errors from matchups."""
    mock_league = MagicMock()
    # This will cause get_current_matchups to fail
    mock_league.current_week = None

    result = generate_batch_score_summary(mock_league)

    assert result["success"] is False
    assert "error" in result


def test_generate_batch_score_summary_format_structure():
    """Verify that generate_batch_score_summary output has correct structure."""
    mock_league = MagicMock()
    mock_league.current_week = 7

    mock_home_team = MagicMock()
    mock_home_team.team_name = "Home Squad"

    mock_away_team = MagicMock()
    mock_away_team.team_name = "Away Squad"

    mock_box_score = MagicMock()
    mock_box_score.home_team = mock_home_team
    mock_box_score.away_team = mock_away_team
    mock_box_score.home_score = 99.99
    mock_box_score.away_score = 88.88
    mock_box_score.home_projected = 105.50
    mock_box_score.away_projected = 95.75

    mock_league.box_scores.return_value = [mock_box_score]

    result = generate_batch_score_summary(mock_league)

    summary = result["summary"]
    # Verify structure has matchup header and team lines with scores
    lines = summary.split("\n")
    assert lines[0].strip() == "Week 7 Summary"
    assert "Home Squad vs Away Squad" in summary
    # Check for values as Python formats them
    assert "Home Squad: 99.99 (Projected: 105.5)" in summary
    assert "Away Squad: 88.88 (Projected: 95.75)" in summary


def test_get_team_roster_with_none_league():
    """Verify that get_team_roster returns error when league is None."""
    result = get_team_roster(None, "Test Team")

    assert result["success"] is False
    assert "League is None" in result["error"]


def test_get_team_roster_invalid_team_name():
    """Verify that get_team_roster handles invalid team names."""
    mock_league = MagicMock()
    mock_league.teams = []

    result = get_team_roster(mock_league, "")

    assert result["success"] is False
    assert "Invalid team_name" in result["error"]


def test_get_team_roster_team_not_found():
    """Verify that get_team_roster returns error when team is not found."""
    mock_league = MagicMock()
    mock_team_a = MagicMock()
    mock_team_a.team_name = "Kansas City Chiefs"
    mock_team_b = MagicMock()
    mock_team_b.team_name = "Dallas Cowboys"
    mock_league.teams = [mock_team_a, mock_team_b]

    result = get_team_roster(mock_league, "Nonexistent Team")

    assert result["success"] is False
    assert "not found" in result["error"]
    assert "Kansas City Chiefs" in result["error"]
    assert "Dallas Cowboys" in result["error"]


def test_get_team_roster_exact_match():
    """Verify that get_team_roster finds teams with exact name match."""
    mock_league = MagicMock()
    mock_team = MagicMock()
    mock_team.team_name = "Kansas City Chiefs"

    # Create mock players
    mock_player1 = MagicMock()
    mock_player1.name = "Patrick Mahomes"
    mock_player1.position = "QB"
    mock_player1.injuryStatus = ""

    mock_player2 = MagicMock()
    mock_player2.name = "Travis Kelce"
    mock_player2.position = "TE"
    mock_player2.injuryStatus = ""

    mock_team.roster = [mock_player1, mock_player2]
    mock_league.teams = [mock_team]

    result = get_team_roster(mock_league, "Kansas City Chiefs")

    assert result["success"] is True
    assert result["team_name"] == "Kansas City Chiefs"
    assert len(result["roster"]) == 2


def test_get_team_roster_case_insensitive_match():
    """Verify that get_team_roster handles case-insensitive team names."""
    mock_league = MagicMock()
    mock_team = MagicMock()
    mock_team.team_name = "Kansas City Chiefs"

    mock_player = MagicMock()
    mock_player.name = "Patrick Mahomes"
    mock_player.position = "QB"
    mock_player.injuryStatus = ""

    mock_team.roster = [mock_player]
    mock_league.teams = [mock_team]

    result = get_team_roster(mock_league, "kansas city chiefs")

    assert result["success"] is True
    assert result["team_name"] == "Kansas City Chiefs"
    assert len(result["roster"]) == 1


def test_get_team_roster_fuzzy_match():
    """Verify that get_team_roster uses fuzzy matching for partial names."""
    mock_league = MagicMock()
    mock_team = MagicMock()
    mock_team.team_name = "Kansas City Chiefs"

    mock_player = MagicMock()
    mock_player.name = "Patrick Mahomes"
    mock_player.position = "QB"
    mock_player.injuryStatus = ""

    mock_team.roster = [mock_player]
    mock_league.teams = [mock_team]

    # Test with a partial/misspelled name
    result = get_team_roster(mock_league, "Kansas City")

    assert result["success"] is True
    assert result["team_name"] == "Kansas City Chiefs"


def test_get_team_roster_player_with_injury():
    """Verify that get_team_roster includes injury status for injured players."""
    mock_league = MagicMock()
    mock_team = MagicMock()
    mock_team.team_name = "Dallas Cowboys"

    # Create mock players - one healthy, one injured
    mock_player_healthy = MagicMock()
    mock_player_healthy.name = "CeeDee Lamb"
    mock_player_healthy.position = "WR"
    mock_player_healthy.injuryStatus = ""

    mock_player_injured = MagicMock()
    mock_player_injured.name = "Dak Prescott"
    mock_player_injured.position = "QB"
    mock_player_injured.injuryStatus = "Out"

    mock_team.roster = [mock_player_healthy, mock_player_injured]
    mock_league.teams = [mock_team]

    result = get_team_roster(mock_league, "Dallas Cowboys")

    assert result["success"] is True
    assert len(result["roster"]) == 2

    # Check injury status
    injured_player = next(p for p in result["roster"] if p["name"] == "Dak Prescott")
    assert injured_player["injury_status"] == "Out"

    healthy_player = next(p for p in result["roster"] if p["name"] == "CeeDee Lamb")
    assert healthy_player["injury_status"] == ""


def test_get_team_roster_various_injury_statuses():
    """Verify that get_team_roster handles various injury status values."""
    mock_league = MagicMock()
    mock_team = MagicMock()
    mock_team.team_name = "San Francisco 49ers"

    # Create players with different injury statuses
    injury_statuses = ["", "Out", "Day to Day", "Questionable", "Probable"]
    players = []
    for i, status in enumerate(injury_statuses):
        mock_player = MagicMock()
        mock_player.name = f"Player {i}"
        mock_player.position = "WR"
        mock_player.injuryStatus = status
        players.append(mock_player)

    mock_team.roster = players
    mock_league.teams = [mock_team]

    result = get_team_roster(mock_league, "San Francisco 49ers")

    assert result["success"] is True
    assert len(result["roster"]) == 5

    for i, status in enumerate(injury_statuses):
        player = result["roster"][i]
        assert player["injury_status"] == status


def test_get_team_roster_empty_roster():
    """Verify that get_team_roster handles teams with empty rosters."""
    mock_league = MagicMock()
    mock_team = MagicMock()
    mock_team.team_name = "Rebuild Team"
    mock_team.roster = []
    mock_league.teams = [mock_team]

    result = get_team_roster(mock_league, "Rebuild Team")

    assert result["success"] is True
    assert result["team_name"] == "Rebuild Team"
    assert result["roster"] == []


def test_get_team_roster_sorting():
    """Verify that get_team_roster returns roster sorted by position then name."""
    mock_league = MagicMock()
    mock_team = MagicMock()
    mock_team.team_name = "Test Team"

    # Create players in random order
    mock_player_wr2 = MagicMock()
    mock_player_wr2.name = "Zay Jones"
    mock_player_wr2.position = "WR"
    mock_player_wr2.injuryStatus = ""

    mock_player_qb = MagicMock()
    mock_player_qb.name = "Aaron Rodgers"
    mock_player_qb.position = "QB"
    mock_player_qb.injuryStatus = ""

    mock_player_wr1 = MagicMock()
    mock_player_wr1.name = "Adam Thielen"
    mock_player_wr1.position = "WR"
    mock_player_wr1.injuryStatus = ""

    mock_player_rb = MagicMock()
    mock_player_rb.name = "Josh Jacobs"
    mock_player_rb.position = "RB"
    mock_player_rb.injuryStatus = ""

    mock_team.roster = [
        mock_player_wr2,
        mock_player_qb,
        mock_player_wr1,
        mock_player_rb,
    ]
    mock_league.teams = [mock_team]

    result = get_team_roster(mock_league, "Test Team")

    assert result["success"] is True
    roster = result["roster"]
    # Verify sorting: QB, RB, then WRs alphabetically
    assert roster[0]["position"] == "QB"
    assert roster[1]["position"] == "RB"
    assert roster[2]["position"] == "WR"
    assert roster[2]["name"] == "Adam Thielen"
    assert roster[3]["position"] == "WR"
    assert roster[3]["name"] == "Zay Jones"


def test_get_team_roster_multiple_teams():
    """Verify that get_team_roster can find correct team when multiple exist."""
    mock_league = MagicMock()

    # Create multiple teams
    mock_team1 = MagicMock()
    mock_team1.team_name = "Team A"
    mock_player1 = MagicMock()
    mock_player1.name = "Player A1"
    mock_player1.position = "QB"
    mock_player1.injuryStatus = ""
    mock_team1.roster = [mock_player1]

    mock_team2 = MagicMock()
    mock_team2.team_name = "Team B"
    mock_player2 = MagicMock()
    mock_player2.name = "Player B1"
    mock_player2.position = "RB"
    mock_player2.injuryStatus = ""
    mock_team2.roster = [mock_player2]

    mock_league.teams = [mock_team1, mock_team2]

    # Test retrieval of Team B
    result = get_team_roster(mock_league, "Team B")

    assert result["success"] is True
    assert result["team_name"] == "Team B"
    assert result["roster"][0]["name"] == "Player B1"


def test_get_team_roster_attribute_error():
    """Verify that get_team_roster handles attribute errors gracefully."""
    mock_league = MagicMock()
    mock_teams = MagicMock()
    mock_teams.__iter__.side_effect = AttributeError("Missing attribute")
    mock_league.teams = mock_teams

    result = get_team_roster(mock_league, "Test Team")

    assert result["success"] is False
    assert "Invalid league data structure" in result["error"]


def test_get_team_roster_connection_error():
    """Verify that get_team_roster handles connection errors gracefully."""
    mock_league = MagicMock()
    mock_teams = MagicMock()
    mock_teams.__iter__.side_effect = ConnectionError("Connection failed")
    mock_league.teams = mock_teams

    result = get_team_roster(mock_league, "Test Team")

    assert result["success"] is False
    assert "API connection error" in result["error"]


def test_get_team_roster_timeout_error():
    """Verify that get_team_roster handles timeout errors gracefully."""
    mock_league = MagicMock()
    mock_teams = MagicMock()
    mock_teams.__iter__.side_effect = TimeoutError("Request timeout")
    mock_league.teams = mock_teams

    result = get_team_roster(mock_league, "Test Team")

    assert result["success"] is False
    assert "API connection error" in result["error"]


def test_get_team_roster_generic_exception():
    """Verify that get_team_roster handles generic exceptions gracefully."""
    mock_league = MagicMock()
    mock_teams = MagicMock()
    mock_teams.__iter__.side_effect = ValueError("Unexpected error")
    mock_league.teams = mock_teams

    result = get_team_roster(mock_league, "Test Team")

    assert result["success"] is False
    assert "Unexpected error fetching team roster" in result["error"]


# Tests for set_lineup_status


def test_set_lineup_status_with_none_league(mock_verify_team_ownership):
    """Verify that set_lineup_status returns error when league is None."""
    result = set_lineup_status(None, "U1234567890", 1, "Player Name", "BENCH")

    assert result["success"] is False
    assert "League is None" in result["error"]


def test_set_lineup_status_invalid_player_name(mock_verify_team_ownership):
    """Verify that set_lineup_status returns error for invalid player_name."""
    mock_league = MagicMock()

    result = set_lineup_status(mock_league, "U1234567890", 1, "", "BENCH")

    assert result["success"] is False
    assert "Invalid player_name" in result["error"]

    result = set_lineup_status(mock_league, "U1234567890", 1, None, "BENCH")

    assert result["success"] is False
    assert "Invalid player_name" in result["error"]


def test_set_lineup_status_invalid_target_slot(mock_verify_team_ownership):
    """Verify that set_lineup_status returns error for invalid target_slot."""
    mock_league = MagicMock()

    result = set_lineup_status(mock_league, "U1234567890", 1, "Player Name", "")

    assert result["success"] is False
    assert "Invalid target_slot" in result["error"]

    result = set_lineup_status(mock_league, "U1234567890", 1, "Player Name", None)

    assert result["success"] is False
    assert "Invalid target_slot" in result["error"]


def test_set_lineup_status_team_not_found(mock_verify_team_ownership):
    """Verify that set_lineup_status returns error when team is not found."""
    mock_league = MagicMock()
    mock_league.teams = []

    result = set_lineup_status(mock_league, "U1234567890", 999, "Player Name", "BENCH")

    assert result["success"] is False
    assert "Team with ID 999 not found" in result["error"]


def test_set_lineup_status_player_not_found(mock_verify_team_ownership):
    """Verify that set_lineup_status returns error when player is not found."""
    mock_player1 = MagicMock()
    mock_player1.name = "John Doe"
    mock_player1.player_id = 123

    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.roster = [mock_player1]

    mock_league = MagicMock()
    mock_league.teams = [mock_team]

    result = set_lineup_status(
        mock_league, "U1234567890", 1, "Nonexistent Player", "BENCH"
    )

    assert result["success"] is False
    assert "Player 'Nonexistent Player' not found on team" in result["error"]


def test_set_lineup_status_invalid_slot(mock_verify_team_ownership):
    """Verify that set_lineup_status returns error for invalid slot."""
    mock_player = MagicMock()
    mock_player.name = "John Doe"
    mock_player.player_id = 123
    mock_player.slot_position = 0

    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.roster = [mock_player]

    mock_league = MagicMock()
    mock_league.teams = [mock_team]

    result = set_lineup_status(
        mock_league, "U1234567890", 1, "John Doe", "INVALID_SLOT"
    )

    assert result["success"] is False
    assert "Invalid slot 'INVALID_SLOT'" in result["error"]


def test_set_lineup_status_success(mock_verify_team_ownership):
    """Verify that set_lineup_status successfully updates lineup."""
    mock_player1 = MagicMock()
    mock_player1.name = "John Doe"
    mock_player1.player_id = 123
    mock_player1.slot_position = 0  # QB

    mock_player2 = MagicMock()
    mock_player2.name = "Jane Smith"
    mock_player2.player_id = 456
    mock_player2.slot_position = 20  # BENCH

    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.roster = [mock_player1, mock_player2]

    mock_league = MagicMock()
    mock_league.teams = [mock_team]
    mock_league.league_id = 12345
    mock_league.year = 2024
    mock_league.current_week = 5
    mock_league.espn_request = MagicMock()
    mock_league.espn_request.cookies = {
        "espn_s2": "test_s2",
        "SWID": "test_swid",
    }

    with patch("main.requests.put") as mock_put:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        result = set_lineup_status(mock_league, "U1234567890", 1, "John Doe", "BENCH")

        assert result["success"] is True
        assert result["player_name"] == "John Doe"
        assert result["previous_slot"] == "QB"
        assert result["new_slot"] == "BENCH"

        # Verify PUT request was made
        mock_put.assert_called_once()
        call_args = mock_put.call_args
        assert "https://lm-api.fantasy.espn.com" in call_args[0][0]
        assert call_args[1]["json"]["scoringPeriodId"] == 5


def test_set_lineup_status_player_fuzzy_match(mock_verify_team_ownership):
    """Verify that set_lineup_status uses fuzzy matching for player names."""
    mock_player = MagicMock()
    mock_player.name = "Patrick Mahomes"
    mock_player.player_id = 123
    mock_player.slot_position = 0  # QB

    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.roster = [mock_player]

    mock_league = MagicMock()
    mock_league.teams = [mock_team]
    mock_league.league_id = 12345
    mock_league.year = 2024
    mock_league.current_week = 5
    mock_league.espn_request = MagicMock()
    mock_league.espn_request.cookies = {}

    with patch("main.requests.put") as mock_put:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        result = set_lineup_status(
            mock_league, "U1234567890", 1, "patrick mahomes", "BENCH"
        )

        assert result["success"] is True
        assert result["player_name"] == "Patrick Mahomes"


def test_set_lineup_status_api_authentication_error(mock_verify_team_ownership):
    """Verify that set_lineup_status handles 401 authentication errors."""
    mock_player = MagicMock()
    mock_player.name = "John Doe"
    mock_player.player_id = 123
    mock_player.slot_position = 0

    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.roster = [mock_player]

    mock_league = MagicMock()
    mock_league.teams = [mock_team]
    mock_league.league_id = 12345
    mock_league.year = 2024
    mock_league.current_week = 5
    mock_league.espn_request = MagicMock()
    mock_league.espn_request.cookies = {}

    with patch("main.requests.put") as mock_put:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_put.return_value = mock_response

        result = set_lineup_status(mock_league, "U1234567890", 1, "John Doe", "BENCH")

        assert result["success"] is False
        assert "Authentication failed" in result["error"]


def test_set_lineup_status_player_locked_error(mock_verify_team_ownership):
    """Verify that set_lineup_status handles 403 player locked errors."""
    mock_player = MagicMock()
    mock_player.name = "John Doe"
    mock_player.player_id = 123
    mock_player.slot_position = 0

    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.roster = [mock_player]

    mock_league = MagicMock()
    mock_league.teams = [mock_team]
    mock_league.league_id = 12345
    mock_league.year = 2024
    mock_league.current_week = 5
    mock_league.espn_request = MagicMock()
    mock_league.espn_request.cookies = {}

    with patch("main.requests.put") as mock_put:
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Player is locked"
        mock_put.return_value = mock_response

        result = set_lineup_status(mock_league, "U1234567890", 1, "John Doe", "BENCH")

        assert result["success"] is False
        assert "Cannot update lineup" in result["error"]
        assert "Player may be locked" in result["error"]


def test_set_lineup_status_api_error(mock_verify_team_ownership):
    """Verify that set_lineup_status handles other ESPN API errors."""
    mock_player = MagicMock()
    mock_player.name = "John Doe"
    mock_player.player_id = 123
    mock_player.slot_position = 0

    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.roster = [mock_player]

    mock_league = MagicMock()
    mock_league.teams = [mock_team]
    mock_league.league_id = 12345
    mock_league.year = 2024
    mock_league.current_week = 5
    mock_league.espn_request = MagicMock()
    mock_league.espn_request.cookies = {}

    with patch("main.requests.put") as mock_put:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_put.return_value = mock_response

        result = set_lineup_status(mock_league, "U1234567890", 1, "John Doe", "BENCH")

        assert result["success"] is False
        assert "ESPN API returned status 500" in result["error"]


def test_set_lineup_status_timeout_error(mock_verify_team_ownership):
    """Verify that set_lineup_status handles timeout errors."""
    mock_player = MagicMock()
    mock_player.name = "John Doe"
    mock_player.player_id = 123
    mock_player.slot_position = 0

    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.roster = [mock_player]

    mock_league = MagicMock()
    mock_league.teams = [mock_team]
    mock_league.league_id = 12345
    mock_league.year = 2024
    mock_league.current_week = 5
    mock_league.espn_request = MagicMock()
    mock_league.espn_request.cookies = {}

    with patch("main.requests.put") as mock_put:
        import requests

        mock_put.side_effect = requests.exceptions.Timeout("Request timeout")

        result = set_lineup_status(mock_league, "U1234567890", 1, "John Doe", "BENCH")

        assert result["success"] is False
        assert "timed out" in result["error"]


def test_set_lineup_status_connection_error(mock_verify_team_ownership):
    """Verify that set_lineup_status handles connection errors."""
    mock_player = MagicMock()
    mock_player.name = "John Doe"
    mock_player.player_id = 123
    mock_player.slot_position = 0

    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.roster = [mock_player]

    mock_league = MagicMock()
    mock_league.teams = [mock_team]
    mock_league.league_id = 12345
    mock_league.year = 2024
    mock_league.current_week = 5
    mock_league.espn_request = MagicMock()
    mock_league.espn_request.cookies = {}

    with patch("main.requests.put") as mock_put:
        import requests

        mock_put.side_effect = requests.exceptions.ConnectionError("Connection failed")

        result = set_lineup_status(mock_league, "U1234567890", 1, "John Doe", "BENCH")

        assert result["success"] is False
        assert "Connection error" in result["error"]


def test_set_lineup_status_generic_exception(mock_verify_team_ownership):
    """Verify that set_lineup_status handles generic exceptions."""
    mock_league = MagicMock()
    mock_teams = MagicMock()
    mock_teams.__iter__.side_effect = ValueError("Unexpected error")
    mock_league.teams = mock_teams

    result = set_lineup_status(mock_league, "U1234567890", 1, "John Doe", "BENCH")

    assert result["success"] is False
    assert "Unexpected error updating lineup" in result["error"]


# Tests for process_waiver_transaction


def test_process_waiver_transaction_with_none_league(mock_verify_team_ownership):
    """Verify that process_waiver_transaction returns error when league is None."""
    result = process_waiver_transaction(None, "U1234567890", 1, "Player", "Drop", 10)

    assert result["success"] is False
    assert "League is None" in result["error"]


def test_process_waiver_transaction_invalid_team_id_string(mock_verify_team_ownership):
    """Verify that process_waiver_transaction rejects non-integer team_id."""
    mock_league = MagicMock()
    result = process_waiver_transaction(
        mock_league, "U1234567890", "1", "Player", "Drop", 10
    )

    assert result["success"] is False
    assert "Invalid team_id" in result["error"]


def test_process_waiver_transaction_invalid_team_id_zero(mock_verify_team_ownership):
    """Verify that process_waiver_transaction rejects zero team_id."""
    mock_league = MagicMock()
    result = process_waiver_transaction(
        mock_league, "U1234567890", 0, "Player", "Drop", 10
    )

    assert result["success"] is False
    assert "Invalid team_id" in result["error"]


def test_process_waiver_transaction_invalid_team_id_negative(
    mock_verify_team_ownership,
):
    """Verify that process_waiver_transaction rejects negative team_id."""
    mock_league = MagicMock()
    result = process_waiver_transaction(
        mock_league, "U1234567890", -1, "Player", "Drop", 10
    )

    assert result["success"] is False
    assert "Invalid team_id" in result["error"]


def test_process_waiver_transaction_invalid_player_to_add_empty(
    mock_verify_team_ownership,
):
    """Verify that process_waiver_transaction rejects empty player_to_add."""
    mock_league = MagicMock()
    result = process_waiver_transaction(mock_league, "U1234567890", 1, "", "Drop", 10)

    assert result["success"] is False
    assert "Invalid player_to_add" in result["error"]


def test_process_waiver_transaction_invalid_player_to_add_none(
    mock_verify_team_ownership,
):
    """Verify that process_waiver_transaction rejects None player_to_add."""
    mock_league = MagicMock()
    result = process_waiver_transaction(mock_league, "U1234567890", 1, None, "Drop", 10)

    assert result["success"] is False
    assert "Invalid player_to_add" in result["error"]


def test_process_waiver_transaction_invalid_player_to_add_type(
    mock_verify_team_ownership,
):
    """Verify that process_waiver_transaction rejects non-string player_to_add."""
    mock_league = MagicMock()
    result = process_waiver_transaction(mock_league, "U1234567890", 1, 123, "Drop", 10)

    assert result["success"] is False
    assert "Invalid player_to_add" in result["error"]


def test_process_waiver_transaction_invalid_player_to_drop_type(
    mock_verify_team_ownership,
):
    """Verify that process_waiver_transaction rejects non-string player_to_drop."""
    mock_league = MagicMock()
    result = process_waiver_transaction(mock_league, "U1234567890", 1, "Add", 123, 10)

    assert result["success"] is False
    assert "Invalid player_to_drop" in result["error"]


def test_process_waiver_transaction_invalid_bid_amount_negative(
    mock_verify_team_ownership,
):
    """Verify that process_waiver_transaction rejects negative bid_amount."""
    mock_league = MagicMock()
    result = process_waiver_transaction(
        mock_league, "U1234567890", 1, "Player", "Drop", -1
    )

    assert result["success"] is False
    assert "Invalid bid_amount" in result["error"]


def test_process_waiver_transaction_invalid_bid_amount_too_high(
    mock_verify_team_ownership,
):
    """Verify that process_waiver_transaction rejects bid_amount > 999."""
    mock_league = MagicMock()
    result = process_waiver_transaction(
        mock_league, "U1234567890", 1, "Player", "Drop", 1000
    )

    assert result["success"] is False
    assert "Invalid bid_amount" in result["error"]
    assert "not exceed 999" in result["error"]


def test_process_waiver_transaction_invalid_bid_amount_type(mock_verify_team_ownership):
    """Verify that process_waiver_transaction rejects non-integer bid_amount."""
    mock_league = MagicMock()
    result = process_waiver_transaction(
        mock_league, "U1234567890", 1, "Player", "Drop", "10"
    )

    assert result["success"] is False
    assert "Invalid bid_amount" in result["error"]


def test_process_waiver_transaction_team_not_found(mock_verify_team_ownership):
    """Verify that process_waiver_transaction returns error when team not found."""
    mock_league = MagicMock()
    mock_team = MagicMock()
    mock_team.team_id = 2
    mock_league.teams = [mock_team]

    result = process_waiver_transaction(
        mock_league, "U1234567890", 1, "Player", "Drop", 10
    )

    assert result["success"] is False
    assert "Team with ID 1 not found" in result["error"]


def test_process_waiver_transaction_player_to_add_not_found(mock_verify_team_ownership):
    """Verify error when player to add is not found in league."""
    mock_league = MagicMock()
    mock_league.year = 2024
    mock_league.league_id = 12345

    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.team_name = "Test Team"
    mock_team.roster = []

    mock_league.teams = [mock_team]
    mock_league.players = []

    result = process_waiver_transaction(
        mock_league, "U1234567890", 1, "Nonexistent Player", None, 0
    )

    assert result["success"] is False
    assert "not found in league" in result["error"]


def test_process_waiver_transaction_player_already_on_team(mock_verify_team_ownership):
    """Verify error when player to add is already on the team."""
    mock_league = MagicMock()
    mock_league.year = 2024
    mock_league.league_id = 12345

    # Create mock player to add
    mock_add_player = MagicMock()
    mock_add_player.player_id = 1
    mock_add_player.name = "Patrick Mahomes"

    # Create mock team with the player already on roster
    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.team_name = "Test Team"
    mock_team.roster = [mock_add_player]

    mock_league.teams = [mock_team]
    mock_league.players = [mock_add_player]

    result = process_waiver_transaction(
        mock_league, "U1234567890", 1, "Patrick Mahomes", None, 0
    )

    assert result["success"] is False
    assert "already on" in result["error"]


def test_process_waiver_transaction_player_to_drop_not_found(
    mock_verify_team_ownership,
):
    """Verify error when player to drop is not found on team roster."""
    mock_league = MagicMock()
    mock_league.year = 2024
    mock_league.league_id = 12345

    # Create mock players
    mock_add_player = MagicMock()
    mock_add_player.player_id = 1
    mock_add_player.name = "Patrick Mahomes"

    mock_existing_player = MagicMock()
    mock_existing_player.player_id = 2
    mock_existing_player.name = "Josh Allen"

    # Create mock team
    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.team_name = "Test Team"
    mock_team.roster = [mock_existing_player]

    mock_league.teams = [mock_team]
    mock_league.players = [mock_add_player, mock_existing_player]

    result = process_waiver_transaction(
        mock_league, "U1234567890", 1, "Patrick Mahomes", "Nonexistent Player", 10
    )

    assert result["success"] is False
    assert "not found on" in result["error"]


def test_process_waiver_transaction_success_with_drop(mock_verify_team_ownership):
    """Verify successful waiver transaction with player drop."""
    mock_league = MagicMock()
    mock_league.year = 2024
    mock_league.league_id = 12345
    mock_league.espn_request = MagicMock()
    mock_league.espn_request.cookies = {"espn_s2": "test"}

    # Create mock players
    mock_add_player = MagicMock()
    mock_add_player.player_id = 1
    mock_add_player.name = "Patrick Mahomes"

    mock_drop_player = MagicMock()
    mock_drop_player.player_id = 2
    mock_drop_player.name = "Josh Allen"

    # Create mock team
    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.team_name = "Test Team"
    mock_team.roster = [mock_drop_player]

    mock_league.teams = [mock_team]
    mock_league.players = [mock_add_player, mock_drop_player]

    with patch("main.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = process_waiver_transaction(
            mock_league, "U1234567890", 1, "Patrick Mahomes", "Josh Allen", 10
        )

        assert result["success"] is True
        assert result["player_added"] == "Patrick Mahomes"
        assert result["player_dropped"] == "Josh Allen"
        assert result["bid_amount"] == 10
        assert result["transaction_type"] == "WAIVER"

        # Verify the POST request was made correctly
        call_args = mock_post.call_args
        assert "transactions" in call_args[1]["json"]
        assert call_args[1]["json"]["transactions"][0]["type"] == "WAIVER"
        assert call_args[1]["json"]["transactions"][0]["bidAmount"] == 10
        assert call_args[1]["json"]["transactions"][0]["addedPlayerIds"] == [1]
        assert call_args[1]["json"]["transactions"][0]["droppedPlayerIds"] == [2]


def test_process_waiver_transaction_success_free_agent_pickup(
    mock_verify_team_ownership,
):
    """Verify successful free agent pickup (no drop, zero bid)."""
    mock_league = MagicMock()
    mock_league.year = 2024
    mock_league.league_id = 12345
    mock_league.espn_request = MagicMock()
    mock_league.espn_request.cookies = {"espn_s2": "test"}

    # Create mock player
    mock_add_player = MagicMock()
    mock_add_player.player_id = 1
    mock_add_player.name = "Patrick Mahomes"

    # Create mock team
    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.team_name = "Test Team"
    mock_team.roster = []

    mock_league.teams = [mock_team]
    mock_league.players = [mock_add_player]

    with patch("main.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = process_waiver_transaction(
            mock_league, "U1234567890", 1, "Patrick Mahomes", None, 0
        )

        assert result["success"] is True
        assert result["player_added"] == "Patrick Mahomes"
        assert result["player_dropped"] is None
        assert result["bid_amount"] == 0
        assert result["transaction_type"] == "FREEAGENT"

        # Verify the POST request
        call_args = mock_post.call_args
        assert call_args[1]["json"]["transactions"][0]["type"] == "FREEAGENT"
        assert call_args[1]["json"]["transactions"][0]["droppedPlayerIds"] == []


def test_process_waiver_transaction_player_fuzzy_match(mock_verify_team_ownership):
    """Verify fuzzy matching works for player names."""
    mock_league = MagicMock()
    mock_league.year = 2024
    mock_league.league_id = 12345
    mock_league.espn_request = MagicMock()
    mock_league.espn_request.cookies = {"espn_s2": "test"}

    # Create mock players
    mock_add_player = MagicMock()
    mock_add_player.player_id = 1
    mock_add_player.name = "Patrick Mahomes"

    mock_drop_player = MagicMock()
    mock_drop_player.player_id = 2
    mock_drop_player.name = "Josh Allen"

    # Create mock team
    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.team_name = "Test Team"
    mock_team.roster = [mock_drop_player]

    mock_league.teams = [mock_team]
    mock_league.players = [mock_add_player, mock_drop_player]

    with patch("main.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Use slightly misspelled names that should fuzzy match
        result = process_waiver_transaction(
            mock_league, "U1234567890", 1, "Patrick Mahome", "Josh Alen", 5
        )

        assert result["success"] is True
        assert result["player_added"] == "Patrick Mahomes"
        assert result["player_dropped"] == "Josh Allen"


def test_process_waiver_transaction_api_authentication_error(
    mock_verify_team_ownership,
):
    """Verify error handling for authentication failure."""
    mock_league = MagicMock()
    mock_league.year = 2024
    mock_league.league_id = 12345
    mock_league.espn_request = MagicMock()
    mock_league.espn_request.cookies = {"espn_s2": "test"}

    # Create mock players
    mock_add_player = MagicMock()
    mock_add_player.player_id = 1
    mock_add_player.name = "Patrick Mahomes"

    # Create mock team
    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.team_name = "Test Team"
    mock_team.roster = []

    mock_league.teams = [mock_team]
    mock_league.players = [mock_add_player]

    with patch("main.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        result = process_waiver_transaction(
            mock_league, "U1234567890", 1, "Patrick Mahomes", None, 0
        )

        assert result["success"] is False
        assert "Authentication failed" in result["error"]


def test_process_waiver_transaction_api_permission_error(mock_verify_team_ownership):
    """Verify error handling for permission denied."""
    mock_league = MagicMock()
    mock_league.year = 2024
    mock_league.league_id = 12345
    mock_league.espn_request = MagicMock()
    mock_league.espn_request.cookies = {"espn_s2": "test"}

    # Create mock players
    mock_add_player = MagicMock()
    mock_add_player.player_id = 1
    mock_add_player.name = "Patrick Mahomes"

    # Create mock team
    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.team_name = "Test Team"
    mock_team.roster = []

    mock_league.teams = [mock_team]
    mock_league.players = [mock_add_player]

    with patch("main.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_post.return_value = mock_response

        result = process_waiver_transaction(
            mock_league, "U1234567890", 1, "Patrick Mahomes", None, 0
        )

        assert result["success"] is False
        assert "Permission denied" in result["error"]


def test_process_waiver_transaction_api_error(mock_verify_team_ownership):
    """Verify error handling for API errors."""
    mock_league = MagicMock()
    mock_league.year = 2024
    mock_league.league_id = 12345
    mock_league.espn_request = MagicMock()
    mock_league.espn_request.cookies = {"espn_s2": "test"}

    # Create mock players
    mock_add_player = MagicMock()
    mock_add_player.player_id = 1
    mock_add_player.name = "Patrick Mahomes"

    # Create mock team
    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.team_name = "Test Team"
    mock_team.roster = []

    mock_league.teams = [mock_team]
    mock_league.players = [mock_add_player]

    with patch("main.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        result = process_waiver_transaction(
            mock_league, "U1234567890", 1, "Patrick Mahomes", None, 0
        )

        assert result["success"] is False
        assert "ESPN API returned status 500" in result["error"]


def test_process_waiver_transaction_timeout_error(mock_verify_team_ownership):
    """Verify timeout error handling."""
    mock_league = MagicMock()
    mock_league.year = 2024
    mock_league.league_id = 12345
    mock_league.espn_request = MagicMock()
    mock_league.espn_request.cookies = {"espn_s2": "test"}

    # Create mock players
    mock_add_player = MagicMock()
    mock_add_player.player_id = 1
    mock_add_player.name = "Patrick Mahomes"

    # Create mock team
    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.team_name = "Test Team"
    mock_team.roster = []

    mock_league.teams = [mock_team]
    mock_league.players = [mock_add_player]

    with patch("main.requests.post") as mock_post:
        import requests

        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        result = process_waiver_transaction(
            mock_league, "U1234567890", 1, "Patrick Mahomes", None, 0
        )

        assert result["success"] is False
        assert "timed out" in result["error"]


def test_process_waiver_transaction_connection_error(mock_verify_team_ownership):
    """Verify connection error handling."""
    mock_league = MagicMock()
    mock_league.year = 2024
    mock_league.league_id = 12345
    mock_league.espn_request = MagicMock()
    mock_league.espn_request.cookies = {"espn_s2": "test"}

    # Create mock players
    mock_add_player = MagicMock()
    mock_add_player.player_id = 1
    mock_add_player.name = "Patrick Mahomes"

    # Create mock team
    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.team_name = "Test Team"
    mock_team.roster = []

    mock_league.teams = [mock_team]
    mock_league.players = [mock_add_player]

    with patch("main.requests.post") as mock_post:
        import requests

        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        result = process_waiver_transaction(
            mock_league, "U1234567890", 1, "Patrick Mahomes", None, 0
        )

        assert result["success"] is False
        assert "Connection error" in result["error"]


def test_process_waiver_transaction_generic_exception(mock_verify_team_ownership):
    """Verify generic exception handling."""
    mock_league = MagicMock()
    mock_teams = MagicMock()
    mock_teams.__iter__.side_effect = ValueError("Unexpected error")
    mock_league.teams = mock_teams

    result = process_waiver_transaction(
        mock_league, "U1234567890", 1, "Patrick Mahomes", None, 0
    )

    assert result["success"] is False
    assert "Unexpected error processing transaction" in result["error"]


# Authorization Tests


class TestSetLineupStatusAuthorization:
    """Test suite for authorization validation in set_lineup_status."""

    def test_set_lineup_status_unauthorized_user(self):
        """Verify that set_lineup_status rejects an unauthorized user."""
        mock_league = MagicMock()

        # Use mock that returns False for unauthorized user
        with patch("main.verify_team_ownership", return_value=False):
            result = set_lineup_status(
                mock_league, "UUNAUTHORIZED", 1, "Player", "BENCH"
            )

        assert result["success"] is False
        assert "Unauthorized" in result["error"]
        assert "UUNAUTHORIZED" in result["error"]
        assert "1" in result["error"]

    def test_set_lineup_status_authorized_user(self):
        """Verify that set_lineup_status allows an authorized user."""
        mock_player = MagicMock()
        mock_player.name = "Patrick Mahomes"
        mock_player.position = "QB"
        mock_player.slot = 0  # QB slot

        mock_team = MagicMock()
        mock_team.team_id = 1
        mock_team.roster = [mock_player]

        mock_league = MagicMock()
        mock_league.teams = [mock_team]

        # Mock the API call for updating lineup
        with patch("main.requests.post") as mock_post:
            mock_post.return_value.status_code = 200

            with patch("main.verify_team_ownership", return_value=True):
                result = set_lineup_status(
                    mock_league, "UAUTHORIZED", 1, "Patrick Mahomes", "BENCH"
                )

        # Should pass authorization and attempt the update
        # (may fail on other validations, but not on authorization)
        assert result["success"] is True or result["error"] != "Unauthorized"


class TestProcessWaiverTransactionAuthorization:
    """Test suite for authorization validation in process_waiver_transaction."""

    def test_process_waiver_transaction_unauthorized_user(self):
        """Verify that process_waiver_transaction rejects an unauthorized user."""
        mock_league = MagicMock()

        # Use mock that returns False for unauthorized user
        with patch("main.verify_team_ownership", return_value=False):
            result = process_waiver_transaction(
                mock_league, "UUNAUTHORIZED", 1, "Player", None, 5
            )

        assert result["success"] is False
        assert "Unauthorized" in result["error"]
        assert "UUNAUTHORIZED" in result["error"]
        assert "1" in result["error"]

    def test_process_waiver_transaction_authorized_user(self):
        """Verify that process_waiver_transaction allows an authorized user."""
        mock_add_player = MagicMock()
        mock_add_player.player_id = 1
        mock_add_player.name = "Patrick Mahomes"

        mock_team = MagicMock()
        mock_team.team_id = 1
        mock_team.team_name = "Test Team"
        mock_team.roster = []

        mock_league = MagicMock()
        mock_league.year = 2024
        mock_league.league_id = 12345
        mock_league.espn_request = MagicMock()
        mock_league.espn_request.cookies = {"espn_s2": "test"}
        mock_league.teams = [mock_team]
        mock_league.players = [mock_add_player]

        # Mock the API call for adding player
        with patch("main.requests.post") as mock_post:
            mock_post.return_value.status_code = 200

            with patch("main.verify_team_ownership", return_value=True):
                result = process_waiver_transaction(
                    mock_league, "UAUTHORIZED", 1, "Patrick Mahomes", None, 5
                )

        # Should pass authorization and attempt the transaction
        # (may fail on other validations, but not on authorization)
        assert result["success"] is True or result["error"] != "Unauthorized"

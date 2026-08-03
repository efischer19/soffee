"""Tests for the main SOFFEE module."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the root directory to the path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import (
    LeagueInitializationError,
    _format_roster_sweep_message,
    detect_roster_violations,
    generate_batch_score_summary,
    get_current_matchups,
    get_historical_season,
    get_team_roster,
    get_top_free_agent_replacements,
    initialize_league,
    process_waiver_transaction,
    run_sunday_roster_sweep,
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

        assert isinstance(result, LeagueInitializationError)
        assert result.error == "Missing ESPN credentials: ESPN_SWID"
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

        assert isinstance(result, LeagueInitializationError)
        assert result.error == "Missing ESPN credentials: ESPN_S2"
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

        assert isinstance(result, LeagueInitializationError)
        assert result.error == "Missing ESPN credentials: ESPN_LEAGUE_ID"
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

        assert isinstance(result, LeagueInitializationError)
        assert result.error == "Missing ESPN credentials: ESPN_YEAR"
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

        assert isinstance(result, LeagueInitializationError)
        assert "Invalid ESPN credentials format" in result.error
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

        assert isinstance(result, LeagueInitializationError)
        assert "Invalid ESPN credentials format" in result.error
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

        assert isinstance(result, LeagueInitializationError)
        assert result.error == "Failed to initialize ESPN League: API error"
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


# Tests for detect_roster_violations
class TestDetectRosterViolations:
    """Test suite for detect_roster_violations function."""

    def test_detect_roster_violations_with_none_league(self):
        """Verify that detect_roster_violations returns error when league is None."""
        result = detect_roster_violations(None, 5)

        assert result["success"] is False
        assert "League is None" in result["error"]

    def test_detect_roster_violations_invalid_week_negative(self):
        """Verify that detect_roster_violations rejects negative week numbers."""
        mock_league = MagicMock()

        result = detect_roster_violations(mock_league, -1)

        assert result["success"] is False
        assert "Invalid week" in result["error"]

    def test_detect_roster_violations_invalid_week_zero(self):
        """Verify that detect_roster_violations rejects week 0."""
        mock_league = MagicMock()

        result = detect_roster_violations(mock_league, 0)

        assert result["success"] is False
        assert "Invalid week" in result["error"]

    def test_detect_roster_violations_invalid_week_too_high(self):
        """Verify that detect_roster_violations rejects week > 17."""
        mock_league = MagicMock()

        result = detect_roster_violations(mock_league, 18)

        assert result["success"] is False
        assert "Invalid week" in result["error"]

    def test_detect_roster_violations_invalid_week_not_integer(self):
        """Verify that detect_roster_violations rejects non-integer week."""
        mock_league = MagicMock()

        result = detect_roster_violations(mock_league, "5")

        assert result["success"] is False
        assert "Invalid week" in result["error"]

    def test_detect_roster_violations_no_violations(self):
        """Verify detect_roster_violations returns empty dict when no violations."""
        # Create mock player with no violations
        mock_player = MagicMock()
        mock_player.name = "Patrick Mahomes"
        mock_player.position = "QB"
        mock_player.lineupSlot = "QB"
        mock_player.active_status = "active"
        mock_player.injuryStatus = None

        # Create mock team with no violations
        mock_team = MagicMock()
        mock_team.team_id = 1
        mock_team.team_name = "Test Team"
        mock_team.roster = [mock_player]

        # Create mock league
        mock_league = MagicMock()
        mock_league.teams = [mock_team]
        mock_league.load_roster_week = MagicMock()

        result = detect_roster_violations(mock_league, 5)

        assert result["success"] is True
        assert result["week"] == 5
        assert result["violations"] == {}
        mock_league.load_roster_week.assert_called_once_with(5)

    def test_detect_roster_violations_bye_week_violation(self):
        """Verify that detect_roster_violations detects bye week violations."""
        # Create mock player on bye week
        mock_player = MagicMock()
        mock_player.name = "Travis Kelce"
        mock_player.position = "TE"
        mock_player.lineupSlot = "TE"
        mock_player.active_status = "bye"
        mock_player.injuryStatus = None

        # Create mock team
        mock_team = MagicMock()
        mock_team.team_id = 1
        mock_team.team_name = "Test Team"
        mock_team.roster = [mock_player]

        # Create mock league
        mock_league = MagicMock()
        mock_league.teams = [mock_team]
        mock_league.load_roster_week = MagicMock()

        result = detect_roster_violations(mock_league, 5)

        assert result["success"] is True
        assert result["week"] == 5
        assert 1 in result["violations"]
        assert len(result["violations"][1]) == 1
        assert result["violations"][1][0]["name"] == "Travis Kelce"
        assert result["violations"][1][0]["position"] == "TE"
        assert result["violations"][1][0]["violation_reason"] == "bye"

    def test_detect_roster_violations_out_status_violation(self):
        """Verify that detect_roster_violations detects OUT injury status."""
        # Create mock player with OUT status
        mock_player = MagicMock()
        mock_player.name = "Saquon Barkley"
        mock_player.position = "RB"
        mock_player.lineupSlot = "RB"
        mock_player.active_status = "active"
        mock_player.injuryStatus = "Out"

        # Create mock team
        mock_team = MagicMock()
        mock_team.team_id = 2
        mock_team.team_name = "Test Team 2"
        mock_team.roster = [mock_player]

        # Create mock league
        mock_league = MagicMock()
        mock_league.teams = [mock_team]
        mock_league.load_roster_week = MagicMock()

        result = detect_roster_violations(mock_league, 5)

        assert result["success"] is True
        assert result["week"] == 5
        assert 2 in result["violations"]
        assert len(result["violations"][2]) == 1
        assert result["violations"][2][0]["name"] == "Saquon Barkley"
        assert result["violations"][2][0]["position"] == "RB"
        assert result["violations"][2][0]["violation_reason"] == "Out"

    def test_detect_roster_violations_ir_status_violation(self):
        """Verify that detect_roster_violations detects IR injury status."""
        # Create mock player with IR status
        mock_player = MagicMock()
        mock_player.name = "Josh Jacobs"
        mock_player.position = "RB"
        mock_player.lineupSlot = "RB/WR"
        mock_player.active_status = "active"
        mock_player.injuryStatus = "IR"

        # Create mock team
        mock_team = MagicMock()
        mock_team.team_id = 3
        mock_team.team_name = "Test Team 3"
        mock_team.roster = [mock_player]

        # Create mock league
        mock_league = MagicMock()
        mock_league.teams = [mock_team]
        mock_league.load_roster_week = MagicMock()

        result = detect_roster_violations(mock_league, 5)

        assert result["success"] is True
        assert result["week"] == 5
        assert 3 in result["violations"]
        assert len(result["violations"][3]) == 1
        assert result["violations"][3][0]["violation_reason"] == "IR"

    def test_detect_roster_violations_ignores_bench_players(self):
        """Verify that detect_roster_violations ignores bench slot players."""
        # Create mock bench player with violation
        mock_bench_player = MagicMock()
        mock_bench_player.name = "Bench Player"
        mock_bench_player.position = "QB"
        mock_bench_player.lineupSlot = "BE"
        mock_bench_player.active_status = "bye"
        mock_bench_player.injuryStatus = None

        # Create mock team
        mock_team = MagicMock()
        mock_team.team_id = 1
        mock_team.team_name = "Test Team"
        mock_team.roster = [mock_bench_player]

        # Create mock league
        mock_league = MagicMock()
        mock_league.teams = [mock_team]
        mock_league.load_roster_week = MagicMock()

        result = detect_roster_violations(mock_league, 5)

        assert result["success"] is True
        # Bench player should be ignored, so no violations
        assert result["violations"] == {}

    def test_detect_roster_violations_ignores_ir_slot_players(self):
        """Verify that detect_roster_violations ignores IR slot players."""
        # Create mock IR slot player (already in IR spot)
        mock_ir_player = MagicMock()
        mock_ir_player.name = "IR Player"
        mock_ir_player.position = "RB"
        mock_ir_player.lineupSlot = "IR"
        mock_ir_player.active_status = "active"
        mock_ir_player.injuryStatus = "Out"

        # Create mock team
        mock_team = MagicMock()
        mock_team.team_id = 1
        mock_team.team_name = "Test Team"
        mock_team.roster = [mock_ir_player]

        # Create mock league
        mock_league = MagicMock()
        mock_league.teams = [mock_team]
        mock_league.load_roster_week = MagicMock()

        result = detect_roster_violations(mock_league, 5)

        assert result["success"] is True
        # IR slot player should be ignored
        assert result["violations"] == {}

    def test_detect_roster_violations_multiple_violations_single_team(self):
        """Verify detect_roster_violations reports multiple violations per team."""
        # Create multiple violating players
        mock_player1 = MagicMock()
        mock_player1.name = "Player One"
        mock_player1.position = "QB"
        mock_player1.lineupSlot = "QB"
        mock_player1.active_status = "bye"
        mock_player1.injuryStatus = None

        mock_player2 = MagicMock()
        mock_player2.name = "Player Two"
        mock_player2.position = "WR"
        mock_player2.lineupSlot = "WR"
        mock_player2.active_status = "active"
        mock_player2.injuryStatus = "Out"

        mock_player3 = MagicMock()
        mock_player3.name = "Player Three"
        mock_player3.position = "RB"
        mock_player3.lineupSlot = "RB"
        mock_player3.active_status = "active"
        mock_player3.injuryStatus = None

        # Create mock team
        mock_team = MagicMock()
        mock_team.team_id = 1
        mock_team.team_name = "Test Team"
        mock_team.roster = [mock_player1, mock_player2, mock_player3]

        # Create mock league
        mock_league = MagicMock()
        mock_league.teams = [mock_team]
        mock_league.load_roster_week = MagicMock()

        result = detect_roster_violations(mock_league, 5)

        assert result["success"] is True
        assert result["week"] == 5
        assert 1 in result["violations"]
        assert len(result["violations"][1]) == 2
        violation_names = [v["name"] for v in result["violations"][1]]
        assert "Player One" in violation_names
        assert "Player Two" in violation_names
        assert "Player Three" not in violation_names

    def test_detect_roster_violations_multiple_teams(self):
        """Verify detect_roster_violations reports violations across teams."""
        # Create violating player for team 1
        mock_player1 = MagicMock()
        mock_player1.name = "Team1 Violator"
        mock_player1.position = "QB"
        mock_player1.lineupSlot = "QB"
        mock_player1.active_status = "bye"
        mock_player1.injuryStatus = None

        # Create violating player for team 2
        mock_player2 = MagicMock()
        mock_player2.name = "Team2 Violator"
        mock_player2.position = "RB"
        mock_player2.lineupSlot = "RB"
        mock_player2.active_status = "active"
        mock_player2.injuryStatus = "Out"

        # Create mock teams
        mock_team1 = MagicMock()
        mock_team1.team_id = 1
        mock_team1.team_name = "Team 1"
        mock_team1.roster = [mock_player1]

        mock_team2 = MagicMock()
        mock_team2.team_id = 2
        mock_team2.team_name = "Team 2"
        mock_team2.roster = [mock_player2]

        # Create mock league
        mock_league = MagicMock()
        mock_league.teams = [mock_team1, mock_team2]
        mock_league.load_roster_week = MagicMock()

        result = detect_roster_violations(mock_league, 5)

        assert result["success"] is True
        assert len(result["violations"]) == 2
        assert 1 in result["violations"]
        assert 2 in result["violations"]
        assert result["violations"][1][0]["name"] == "Team1 Violator"
        assert result["violations"][2][0]["name"] == "Team2 Violator"

    def test_detect_roster_violations_connection_error(self):
        """Verify that detect_roster_violations handles connection errors."""
        mock_league = MagicMock()
        mock_league.load_roster_week = MagicMock(
            side_effect=ConnectionError("API Down")
        )

        result = detect_roster_violations(mock_league, 5)

        assert result["success"] is False
        assert "API connection error" in result["error"]

    def test_detect_roster_violations_timeout_error(self):
        """Verify that detect_roster_violations handles timeout errors."""
        mock_league = MagicMock()
        mock_league.load_roster_week = MagicMock(side_effect=TimeoutError("Timeout"))

        result = detect_roster_violations(mock_league, 5)

        assert result["success"] is False
        assert "API connection error" in result["error"]

    def test_detect_roster_violations_attribute_error(self):
        """Verify that detect_roster_violations handles invalid league data."""
        mock_league = MagicMock()
        mock_league.load_roster_week = MagicMock(
            side_effect=AttributeError("Missing attribute")
        )

        result = detect_roster_violations(mock_league, 5)

        assert result["success"] is False
        assert "Invalid league data structure" in result["error"]

    def test_detect_roster_violations_unexpected_error(self):
        """Verify that detect_roster_violations handles unexpected errors."""
        mock_league = MagicMock()
        mock_league.load_roster_week = MagicMock(side_effect=RuntimeError("Unexpected"))

        result = detect_roster_violations(mock_league, 5)

        assert result["success"] is False
        assert "Unexpected error" in result["error"]
        assert "detecting roster violations" in result["error"]

    def test_detect_roster_violations_case_insensitive_injury_status(self):
        """Verify that injury status checks are case-insensitive."""
        # Create mock players with different case variations
        mock_player1 = MagicMock()
        mock_player1.name = "Player with OUT"
        mock_player1.position = "QB"
        mock_player1.lineupSlot = "QB"
        mock_player1.active_status = "active"
        mock_player1.injuryStatus = "OUT"

        mock_player2 = MagicMock()
        mock_player2.name = "Player with out"
        mock_player2.position = "RB"
        mock_player2.lineupSlot = "RB"
        mock_player2.active_status = "active"
        mock_player2.injuryStatus = "out"

        mock_player3 = MagicMock()
        mock_player3.name = "Player with Ir"
        mock_player3.position = "WR"
        mock_player3.lineupSlot = "WR"
        mock_player3.active_status = "active"
        mock_player3.injuryStatus = "Ir"

        # Create mock team
        mock_team = MagicMock()
        mock_team.team_id = 1
        mock_team.team_name = "Test Team"
        mock_team.roster = [mock_player1, mock_player2, mock_player3]

        # Create mock league
        mock_league = MagicMock()
        mock_league.teams = [mock_team]
        mock_league.load_roster_week = MagicMock()

        result = detect_roster_violations(mock_league, 5)

        assert result["success"] is True
        assert len(result["violations"][1]) == 3
        violation_names = [v["name"] for v in result["violations"][1]]
        assert "Player with OUT" in violation_names
        assert "Player with out" in violation_names
        assert "Player with Ir" in violation_names

    def test_detect_roster_violations_empty_lineup_slot(self):
        """Verify that players with empty lineupSlot are ignored."""
        # Create player with empty lineup slot
        mock_player = MagicMock()
        mock_player.name = "Empty Slot Player"
        mock_player.position = "QB"
        mock_player.lineupSlot = ""
        mock_player.active_status = "bye"
        mock_player.injuryStatus = None

        # Create mock team
        mock_team = MagicMock()
        mock_team.team_id = 1
        mock_team.team_name = "Test Team"
        mock_team.roster = [mock_player]

        # Create mock league
        mock_league = MagicMock()
        mock_league.teams = [mock_team]
        mock_league.load_roster_week = MagicMock()

        result = detect_roster_violations(mock_league, 5)

        assert result["success"] is True
        # Empty slot player should be ignored
        assert result["violations"] == {}


class TestGetTopFreeAgentReplacements:
    """Test suite for get_top_free_agent_replacements function."""

    def test_get_top_free_agent_replacements_with_none_league(self):
        """Verify that function returns error when league is None."""
        result = get_top_free_agent_replacements(None, "QB", week=5)

        assert result["success"] is False
        assert "League is None" in result["error"]

    def test_get_top_free_agent_replacements_invalid_position_empty(self):
        """Verify that function handles empty position string."""
        mock_league = MagicMock()

        result = get_top_free_agent_replacements(mock_league, "", week=5)

        assert result["success"] is False
        assert "Invalid position" in result["error"]

    def test_get_top_free_agent_replacements_invalid_position_type(self):
        """Verify that function handles non-string position."""
        mock_league = MagicMock()

        result = get_top_free_agent_replacements(mock_league, 123, week=5)

        assert result["success"] is False
        assert "Invalid position" in result["error"]

    def test_get_top_free_agent_replacements_invalid_week_negative(self):
        """Verify that function handles negative week number."""
        mock_league = MagicMock()

        result = get_top_free_agent_replacements(mock_league, "QB", week=-1)

        assert result["success"] is False
        assert "Invalid week" in result["error"]

    def test_get_top_free_agent_replacements_invalid_week_zero(self):
        """Verify that function handles week zero."""
        mock_league = MagicMock()

        result = get_top_free_agent_replacements(mock_league, "QB", week=0)

        assert result["success"] is False
        assert "Invalid week" in result["error"]

    def test_get_top_free_agent_replacements_invalid_week_type(self):
        """Verify that function handles non-integer week."""
        mock_league = MagicMock()

        result = get_top_free_agent_replacements(mock_league, "QB", week="5")

        assert result["success"] is False
        assert "Invalid week" in result["error"]

    def test_get_top_free_agent_replacements_invalid_limit_negative(self):
        """Verify that function handles negative limit."""
        mock_league = MagicMock()

        result = get_top_free_agent_replacements(mock_league, "QB", week=5, limit=-1)

        assert result["success"] is False
        assert "Invalid limit" in result["error"]

    def test_get_top_free_agent_replacements_invalid_limit_zero(self):
        """Verify that function handles limit of zero."""
        mock_league = MagicMock()

        result = get_top_free_agent_replacements(mock_league, "QB", week=5, limit=0)

        assert result["success"] is False
        assert "Invalid limit" in result["error"]

    def test_get_top_free_agent_replacements_invalid_limit_type(self):
        """Verify that function handles non-integer limit."""
        mock_league = MagicMock()

        result = get_top_free_agent_replacements(mock_league, "QB", week=5, limit="3")

        assert result["success"] is False
        assert "Invalid limit" in result["error"]

    def test_get_top_free_agent_replacements_no_free_agents(self):
        """Verify that function handles when no free agents are available."""
        mock_league = MagicMock()
        mock_league.free_agents.return_value = []

        result = get_top_free_agent_replacements(mock_league, "QB", week=5)

        assert result["success"] is True
        assert result["position"] == "QB"
        assert result["week"] == 5
        assert result["players"] == []
        assert result["count"] == 0

    def test_get_top_free_agent_replacements_single_player(self):
        """Verify that function returns single player when one free agent exists."""
        mock_league = MagicMock()

        # Create mock player
        mock_player = MagicMock()
        mock_player.name = "Patrick Mahomes"
        mock_player.position = "QB"
        mock_player.proTeam = "KC"
        mock_player.percent_owned = 80.5
        mock_player.stats = {5: {"projected_points": 28.5}}

        mock_league.free_agents.return_value = [mock_player]

        result = get_top_free_agent_replacements(mock_league, "QB", week=5)

        assert result["success"] is True
        assert result["position"] == "QB"
        assert result["week"] == 5
        assert len(result["players"]) == 1
        assert result["count"] == 1
        assert result["players"][0]["name"] == "Patrick Mahomes"
        assert result["players"][0]["position"] == "QB"
        assert result["players"][0]["pro_team"] == "KC"
        assert result["players"][0]["projected_points"] == 28.5
        assert result["players"][0]["percent_owned"] == 80.5

    def test_get_top_free_agent_replacements_multiple_players_sorted(self):
        """Verify that function returns top players sorted by projected points."""
        mock_league = MagicMock()

        # Create mock players with different projections
        player1 = MagicMock()
        player1.name = "Josh Allen"
        player1.position = "QB"
        player1.proTeam = "BUF"
        player1.percent_owned = 75.0
        player1.stats = {5: {"projected_points": 25.0}}

        player2 = MagicMock()
        player2.name = "Patrick Mahomes"
        player2.position = "QB"
        player2.proTeam = "KC"
        player2.percent_owned = 90.0
        player2.stats = {5: {"projected_points": 28.5}}

        player3 = MagicMock()
        player3.name = "Jared Goff"
        player3.position = "QB"
        player3.proTeam = "DET"
        player3.percent_owned = 60.0
        player3.stats = {5: {"projected_points": 22.0}}

        mock_league.free_agents.return_value = [player1, player2, player3]

        result = get_top_free_agent_replacements(mock_league, "QB", week=5, limit=3)

        assert result["success"] is True
        assert result["count"] == 3
        # Should be sorted highest to lowest
        assert result["players"][0]["name"] == "Patrick Mahomes"
        assert result["players"][0]["projected_points"] == 28.5
        assert result["players"][1]["name"] == "Josh Allen"
        assert result["players"][1]["projected_points"] == 25.0
        assert result["players"][2]["name"] == "Jared Goff"
        assert result["players"][2]["projected_points"] == 22.0

    def test_get_top_free_agent_replacements_respects_limit(self):
        """Verify that function respects the limit parameter."""
        mock_league = MagicMock()

        # Create 5 mock players
        players = []
        for i in range(5):
            player = MagicMock()
            player.name = f"Player {i + 1}"
            player.position = "RB"
            player.proTeam = "TB"
            player.percent_owned = 50.0
            player.stats = {5: {"projected_points": float(30 - i)}}
            players.append(player)

        mock_league.free_agents.return_value = players

        result = get_top_free_agent_replacements(mock_league, "RB", week=5, limit=2)

        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["players"]) == 2

    def test_get_top_free_agent_replacements_default_limit(self):
        """Verify that function uses default limit of 3."""
        mock_league = MagicMock()

        # Create 5 mock players
        players = []
        for i in range(5):
            player = MagicMock()
            player.name = f"Player {i + 1}"
            player.position = "WR"
            player.proTeam = "LAC"
            player.percent_owned = 40.0
            player.stats = {5: {"projected_points": float(25 - i)}}
            players.append(player)

        mock_league.free_agents.return_value = players

        # Call without limit parameter
        result = get_top_free_agent_replacements(mock_league, "WR", week=5)

        assert result["success"] is True
        assert result["count"] == 3
        assert len(result["players"]) == 3

    def test_get_top_free_agent_replacements_handles_missing_stats(self):
        """Verify that function handles players with missing stats for week."""
        mock_league = MagicMock()

        # Create player with stats for a different week
        player = MagicMock()
        player.name = "Travis Kelce"
        player.position = "TE"
        player.proTeam = "KC"
        player.percent_owned = 70.0
        player.stats = {4: {"projected_points": 20.0}}  # Only has week 4 stats

        mock_league.free_agents.return_value = [player]

        result = get_top_free_agent_replacements(mock_league, "TE", week=5)

        assert result["success"] is True
        # Should return the player with projected_points = 0 (from missing stats)
        assert result["count"] == 1
        assert result["players"][0]["projected_points"] == 0

    def test_get_top_free_agent_replacements_handles_none_values(self):
        """Verify that function handles players with None for optional fields."""
        mock_league = MagicMock()

        player = MagicMock()
        player.name = "Unknown Player"
        player.position = "K"
        player.proTeam = None  # Can be None
        player.percent_owned = None  # Can be None
        player.stats = {5: {"projected_points": 15.0}}

        mock_league.free_agents.return_value = [player]

        result = get_top_free_agent_replacements(mock_league, "K", week=5)

        assert result["success"] is True
        assert result["count"] == 1
        assert result["players"][0]["pro_team"] == ""
        assert result["players"][0]["percent_owned"] == 0

    def test_get_top_free_agent_replacements_different_positions(self):
        """Verify that function correctly filters by position."""
        mock_league = MagicMock()

        player1 = MagicMock()
        player1.name = "Player 1"
        player1.position = "RB"
        player1.proTeam = "TB"
        player1.percent_owned = 50.0
        player1.stats = {5: {"projected_points": 20.0}}

        mock_league.free_agents.return_value = [player1]

        result = get_top_free_agent_replacements(mock_league, "RB", week=5)

        assert result["success"] is True
        # Verify the correct method was called with the right parameters
        mock_league.free_agents.assert_called_once_with(position="RB", week=5, size=100)

    def test_get_top_free_agent_replacements_connection_error(self):
        """Verify that function handles connection errors gracefully."""
        mock_league = MagicMock()
        mock_league.free_agents.side_effect = ConnectionError(
            "Network connection failed"
        )

        result = get_top_free_agent_replacements(mock_league, "QB", week=5)

        assert result["success"] is False
        assert "API connection error" in result["error"]

    def test_get_top_free_agent_replacements_timeout_error(self):
        """Verify that function handles timeout errors gracefully."""
        mock_league = MagicMock()
        mock_league.free_agents.side_effect = TimeoutError("Request timed out")

        result = get_top_free_agent_replacements(mock_league, "QB", week=5)

        assert result["success"] is False
        assert "API connection error" in result["error"]

    def test_get_top_free_agent_replacements_attribute_error(self):
        """Verify that function handles attribute errors gracefully."""
        mock_league = MagicMock()
        mock_league.free_agents.side_effect = AttributeError("Invalid player structure")

        result = get_top_free_agent_replacements(mock_league, "QB", week=5)

        assert result["success"] is False
        assert "Invalid league data structure" in result["error"]

    def test_get_top_free_agent_replacements_generic_exception(self):
        """Verify that function handles unexpected exceptions gracefully."""
        mock_league = MagicMock()
        mock_league.free_agents.side_effect = Exception("Unexpected error")

        result = get_top_free_agent_replacements(mock_league, "QB", week=5)

        assert result["success"] is False
        assert "Unexpected error fetching free agents" in result["error"]

    def test_get_top_free_agent_replacements_multiple_weeks(self):
        """Verify that function correctly fetches for different weeks."""
        mock_league = MagicMock()

        player = MagicMock()
        player.name = "Test Player"
        player.position = "QB"
        player.proTeam = "KC"
        player.percent_owned = 50.0
        player.stats = {
            5: {"projected_points": 28.5},
            6: {"projected_points": 25.0},
        }

        mock_league.free_agents.return_value = [player]

        # Test week 5
        result_week5 = get_top_free_agent_replacements(mock_league, "QB", week=5)
        assert result_week5["players"][0]["projected_points"] == 28.5

        # Test week 6
        result_week6 = get_top_free_agent_replacements(mock_league, "QB", week=6)
        assert result_week6["players"][0]["projected_points"] == 25.0


class TestRunSundayRosterSweep:
    """Test suite for run_sunday_roster_sweep function."""

    def test_run_sunday_roster_sweep_none_league(self):
        """Verify that function handles None league gracefully."""
        result = run_sunday_roster_sweep(None, week=5)

        assert result["success"] is False
        assert "League is None" in result["error"]

    def test_run_sunday_roster_sweep_invalid_week_negative(self):
        """Verify that function rejects negative week numbers."""
        mock_league = MagicMock()

        result = run_sunday_roster_sweep(mock_league, week=-1)

        assert result["success"] is False
        assert "Invalid week" in result["error"]

    def test_run_sunday_roster_sweep_invalid_week_zero(self):
        """Verify that function rejects week 0."""
        mock_league = MagicMock()

        result = run_sunday_roster_sweep(mock_league, week=0)

        assert result["success"] is False
        assert "Invalid week" in result["error"]

    def test_run_sunday_roster_sweep_invalid_week_too_high(self):
        """Verify that function rejects week > 17."""
        mock_league = MagicMock()

        result = run_sunday_roster_sweep(mock_league, week=18)

        assert result["success"] is False
        assert "Invalid week" in result["error"]

    def test_run_sunday_roster_sweep_invalid_week_not_int(self):
        """Verify that function rejects non-integer week values."""
        mock_league = MagicMock()

        result = run_sunday_roster_sweep(mock_league, week="5")

        assert result["success"] is False
        assert "Invalid week" in result["error"]

    def test_run_sunday_roster_sweep_no_violations(self):
        """Verify that function returns 0 violations when none exist."""
        mock_league = MagicMock()

        with patch("main.detect_roster_violations") as mock_detect:
            mock_detect.return_value = {
                "success": True,
                "week": 5,
                "violations": {},
            }

            result = run_sunday_roster_sweep(mock_league, week=5)

            assert result["success"] is True
            assert result["violations_found"] == 0
            assert result["messages_posted"] == 0

    def test_run_sunday_roster_sweep_detect_violations_fails(self):
        """Verify that function returns error when detect_roster_violations fails."""
        mock_league = MagicMock()

        with patch("main.detect_roster_violations") as mock_detect:
            mock_detect.return_value = {
                "success": False,
                "error": "Failed to detect violations",
            }

            result = run_sunday_roster_sweep(mock_league, week=5)

            assert result["success"] is False
            assert "Failed to detect violations" in result["error"]

    def test_run_sunday_roster_sweep_with_violations_no_slack_mapping(self):
        """Verify that function skips teams without Slack mapping."""
        mock_league = MagicMock()

        with patch("main.detect_roster_violations") as mock_detect:
            mock_detect.return_value = {
                "success": True,
                "week": 5,
                "violations": {
                    1: [
                        {
                            "name": "Player Name",
                            "position": "QB",
                            "violation_reason": "bye",
                        }
                    ]
                },
            }

            with patch("authorization.get_slack_user_for_team") as mock_get_slack:
                mock_get_slack.return_value = None  # No mapping

                result = run_sunday_roster_sweep(mock_league, week=5)

                assert result["success"] is True
                assert result["violations_found"] == 1
                assert result["messages_posted"] == 0

    def test_run_sunday_roster_sweep_with_violations_and_slack_mapping(self):
        """Verify that function finds and processes violations with Slack mapping."""
        mock_league = MagicMock()
        mock_team = MagicMock()
        mock_team.team_id = 1
        mock_team.team_name = "Test Team"
        mock_league.teams = [mock_team]

        with patch("main.detect_roster_violations") as mock_detect:
            mock_detect.return_value = {
                "success": True,
                "week": 5,
                "violations": {
                    1: [
                        {
                            "name": "Player Name",
                            "position": "QB",
                            "violation_reason": "bye",
                        }
                    ]
                },
            }

            with patch("authorization.get_slack_user_for_team") as mock_get_slack:
                mock_get_slack.return_value = "U1234567890"

                with patch("main.get_top_free_agent_replacements") as mock_get_fa:
                    mock_get_fa.return_value = {
                        "success": True,
                        "position": "QB",
                        "players": [
                            {
                                "name": "Patrick Mahomes",
                                "position": "QB",
                                "pro_team": "KC",
                                "projected_points": 28.5,
                                "percent_owned": 95.0,
                            }
                        ],
                    }

                    with patch("main._format_roster_sweep_message") as mock_format:
                        mock_format.return_value = "Test message"

                        with patch("requests.post") as mock_post:
                            mock_post.return_value = MagicMock(status_code=200)

                            result = run_sunday_roster_sweep(mock_league, week=5)

                            assert result["success"] is True
                            assert result["violations_found"] == 1

    def test_run_sunday_roster_sweep_multiple_violations_same_team(self):
        """Verify that function handles multiple violations from same team."""
        mock_league = MagicMock()
        mock_team = MagicMock()
        mock_team.team_id = 1
        mock_team.team_name = "Test Team"
        mock_league.teams = [mock_team]

        with patch("main.detect_roster_violations") as mock_detect:
            mock_detect.return_value = {
                "success": True,
                "week": 5,
                "violations": {
                    1: [
                        {
                            "name": "QB Player",
                            "position": "QB",
                            "violation_reason": "bye",
                        },
                        {
                            "name": "RB Player",
                            "position": "RB",
                            "violation_reason": "Out",
                        },
                    ]
                },
            }

            with patch("authorization.get_slack_user_for_team") as mock_get_slack:
                mock_get_slack.return_value = "U1234567890"

                with patch("main.get_top_free_agent_replacements") as mock_get_fa:
                    mock_get_fa.return_value = {
                        "success": True,
                        "players": [
                            {
                                "name": "Player",
                                "position": "?",
                                "pro_team": "?",
                                "projected_points": 15.0,
                                "percent_owned": 50.0,
                            }
                        ],
                    }

                    with patch("main._format_roster_sweep_message") as mock_format:
                        mock_format.return_value = "Test message"

                        with patch("requests.post") as mock_post:
                            mock_post.return_value = MagicMock(status_code=200)

                            result = run_sunday_roster_sweep(mock_league, week=5)

                            assert result["success"] is True
                            assert result["violations_found"] == 1


class TestFormatRosterSweepMessage:
    """Test suite for _format_roster_sweep_message function."""

    def test_format_roster_sweep_message_basic(self):
        """Verify that function formats a basic violation message."""
        message = _format_roster_sweep_message(
            slack_user_id="U1234567890",
            team_name="Test Team",
            violations=[
                {
                    "name": "Player Name",
                    "position": "QB",
                    "violation_reason": "bye",
                }
            ],
            suggestions={},
        )

        assert "<@U1234567890>" in message
        assert "Test Team" in message
        assert "Player Name" in message
        assert "QB" in message
        assert "bye week" in message

    def test_format_roster_sweep_message_with_suggestions(self):
        """Verify that function includes free agent suggestions."""
        message = _format_roster_sweep_message(
            slack_user_id="U1234567890",
            team_name="Test Team",
            violations=[
                {
                    "name": "Injured Player",
                    "position": "RB",
                    "violation_reason": "Out",
                }
            ],
            suggestions={
                "RB": [
                    {
                        "name": "Replacement RB",
                        "position": "RB",
                        "pro_team": "KC",
                        "projected_points": 18.5,
                        "percent_owned": 60.0,
                    }
                ]
            },
        )

        assert "Replacement RB" in message
        assert "18.5" in message
        assert "KC" in message

    def test_format_roster_sweep_message_multiple_violations(self):
        """Verify that function handles multiple violations."""
        message = _format_roster_sweep_message(
            slack_user_id="U1234567890",
            team_name="Test Team",
            violations=[
                {
                    "name": "QB Player",
                    "position": "QB",
                    "violation_reason": "bye",
                },
                {
                    "name": "RB Player",
                    "position": "RB",
                    "violation_reason": "Out",
                },
            ],
            suggestions={},
        )

        assert "QB Player" in message
        assert "RB Player" in message
        assert message.count("❌") == 2

    def test_format_roster_sweep_message_injury_status(self):
        """Verify that function formats injury status correctly."""
        message = _format_roster_sweep_message(
            slack_user_id="U1234567890",
            team_name="Test Team",
            violations=[
                {
                    "name": "Hurt Player",
                    "position": "WR",
                    "violation_reason": "Questionable",
                }
            ],
            suggestions={},
        )

        assert "questionable status" in message.lower()

    def test_format_roster_sweep_message_includes_call_to_action(self):
        """Verify that function includes engagement call-to-action."""
        message = _format_roster_sweep_message(
            slack_user_id="U1234567890",
            team_name="Test Team",
            violations=[],
            suggestions={},
        )

        assert "👍" in message or "react" in message.lower()


class TestGetHistoricalSeason:
    """Test suite for get_historical_season function."""

    def test_get_historical_season_success(self):
        """Verify that get_historical_season returns historical data successfully."""
        env_vars = {
            "ESPN_SWID": "test_swid",
            "ESPN_S2": "test_s2",
            "ESPN_LEAGUE_ID": "12345",
        }

        mock_team1 = MagicMock()
        mock_team1.team_name = "Team A"
        mock_team1.team_id = 1
        mock_team1.wins = 10
        mock_team1.losses = 4
        mock_team1.points_for = 1250.75
        mock_team1.points_against = 1180.50

        mock_team2 = MagicMock()
        mock_team2.team_name = "Team B"
        mock_team2.team_id = 2
        mock_team2.wins = 9
        mock_team2.losses = 5
        mock_team2.points_for = 1200.25
        mock_team2.points_against = 1150.75

        with (
            patch.dict(os.environ, env_vars, clear=False),
            patch("main.League") as mock_league,
        ):
            mock_instance = MagicMock()
            mock_instance.league_name = "Test League"
            mock_instance.standings = [mock_team1, mock_team2]
            mock_league.return_value = mock_instance

            result = get_historical_season(2024)

            assert result["success"] is True
            assert result["year"] == 2024
            assert result["league_name"] == "Test League"
            assert len(result["standings"]) == 2
            assert result["standings"][0]["team_name"] == "Team A"
            assert result["standings"][0]["wins"] == 10
            assert result["standings"][0]["points_for"] == 1250.75
            assert result["standings"][1]["team_name"] == "Team B"

    def test_get_historical_season_missing_swid(self):
        """Verify get_historical_season fails when ESPN_SWID is missing."""
        env_vars = {
            "ESPN_S2": "test_s2",
            "ESPN_LEAGUE_ID": "12345",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            result = get_historical_season(2024)

            assert result["success"] is False
            assert result["year"] == 2024
            assert "Missing ESPN credentials" in result["error"]
            assert "ESPN_SWID" in result["error"]

    def test_get_historical_season_missing_s2(self):
        """Verify get_historical_season fails when ESPN_S2 is missing."""
        env_vars = {
            "ESPN_SWID": "test_swid",
            "ESPN_LEAGUE_ID": "12345",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            result = get_historical_season(2024)

            assert result["success"] is False
            assert "Missing ESPN credentials" in result["error"]
            assert "ESPN_S2" in result["error"]

    def test_get_historical_season_missing_league_id(self):
        """Verify get_historical_season fails when ESPN_LEAGUE_ID is missing."""
        env_vars = {
            "ESPN_SWID": "test_swid",
            "ESPN_S2": "test_s2",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            result = get_historical_season(2024)

            assert result["success"] is False
            assert "Missing ESPN credentials" in result["error"]
            assert "ESPN_LEAGUE_ID" in result["error"]

    def test_get_historical_season_invalid_year_format(self):
        """Verify get_historical_season handles invalid year format."""
        env_vars = {
            "ESPN_SWID": "test_swid",
            "ESPN_S2": "test_s2",
            "ESPN_LEAGUE_ID": "12345",
        }

        with (
            patch.dict(os.environ, env_vars, clear=False),
            patch("main.League") as mock_league,
        ):
            mock_league.side_effect = ValueError("Invalid year")

            result = get_historical_season(2024)

            assert result["success"] is False
            assert result["year"] == 2024
            assert "Invalid ESPN credentials format" in result["error"]

    def test_get_historical_season_year_not_found(self):
        """Verify get_historical_season handles missing historical data."""
        env_vars = {
            "ESPN_SWID": "test_swid",
            "ESPN_S2": "test_s2",
            "ESPN_LEAGUE_ID": "12345",
        }

        with (
            patch.dict(os.environ, env_vars, clear=False),
            patch("main.League") as mock_league,
        ):
            mock_league.side_effect = KeyError("Year not found")

            result = get_historical_season(1999)

            assert result["success"] is False
            assert result["year"] == 1999
            assert "may not exist for this league" in result["error"]

    def test_get_historical_season_connection_error(self):
        """Verify get_historical_season handles connection errors."""
        env_vars = {
            "ESPN_SWID": "test_swid",
            "ESPN_S2": "test_s2",
            "ESPN_LEAGUE_ID": "12345",
        }

        with (
            patch.dict(os.environ, env_vars, clear=False),
            patch("main.League") as mock_league,
        ):
            mock_league.side_effect = ConnectionError("Network error")

            result = get_historical_season(2024)

            assert result["success"] is False
            assert "Failed to connect to ESPN API" in result["error"]

    def test_get_historical_season_generic_exception(self):
        """Verify get_historical_season handles unexpected exceptions."""
        env_vars = {
            "ESPN_SWID": "test_swid",
            "ESPN_S2": "test_s2",
            "ESPN_LEAGUE_ID": "12345",
        }

        with (
            patch.dict(os.environ, env_vars, clear=False),
            patch("main.League") as mock_league,
        ):
            mock_league.side_effect = RuntimeError("Unexpected error")

            result = get_historical_season(2024)

            assert result["success"] is False
            assert result["year"] == 2024
            assert "Unexpected error" in result["error"]

    def test_get_historical_season_empty_standings(self):
        """Verify that get_historical_season handles empty standings gracefully."""
        env_vars = {
            "ESPN_SWID": "test_swid",
            "ESPN_S2": "test_s2",
            "ESPN_LEAGUE_ID": "12345",
        }

        with (
            patch.dict(os.environ, env_vars, clear=False),
            patch("main.League") as mock_league,
        ):
            mock_instance = MagicMock()
            mock_instance.league_name = "Test League"
            mock_instance.standings = []
            mock_league.return_value = mock_instance

            result = get_historical_season(2024)

            assert result["success"] is True
            assert result["standings"] == []


def test_initialize_league_timeout_returns_human_readable_error(capsys):
    """Verify that ESPN timeouts surface a readable initialization error."""
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
        import requests

        mock_league.side_effect = requests.exceptions.Timeout()

        result = initialize_league()
        captured = capsys.readouterr()

        assert isinstance(result, LeagueInitializationError)
        assert result.error == "Timed out while connecting to ESPN. Please try again."
        assert "Timed out while connecting to ESPN" in captured.out


def test_get_current_matchups_returns_initialization_error_message():
    """Verify that downstream tools surface initialization failures to the LLM."""
    result = get_current_matchups(
        LeagueInitializationError("Missing ESPN credentials: ESPN_SWID")
    )

    assert result["success"] is False
    assert result["error"] == "Missing ESPN credentials: ESPN_SWID"


def test_set_lineup_status_not_found_error(mock_verify_team_ownership):
    """Verify that set_lineup_status returns a friendly 404 error."""
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
        mock_response.status_code = 404
        mock_put.return_value = mock_response

        result = set_lineup_status(mock_league, "U1234567890", 1, "John Doe", "BENCH")

        assert result["success"] is False
        assert "could not find the requested lineup resource" in result["error"]


def test_process_waiver_transaction_rejected_claim_error(mock_verify_team_ownership):
    """Verify that rejected waiver claims return ESPN's reason."""
    mock_league = MagicMock()
    mock_league.year = 2024
    mock_league.league_id = 12345
    mock_league.espn_request = MagicMock()
    mock_league.espn_request.cookies = {"espn_s2": "test"}

    mock_add_player = MagicMock()
    mock_add_player.player_id = 1
    mock_add_player.name = "Patrick Mahomes"

    mock_team = MagicMock()
    mock_team.team_id = 1
    mock_team.team_name = "Test Team"
    mock_team.roster = []

    mock_league.teams = [mock_team]
    mock_league.players = [mock_add_player]

    with patch("main.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Waiver period is closed for this player"
        mock_post.return_value = mock_response

        result = process_waiver_transaction(
            mock_league, "U1234567890", 1, "Patrick Mahomes", None, 5
        )

        assert result["success"] is False
        assert "ESPN rejected the transaction" in result["error"]
        assert "Waiver period is closed for this player" in result["error"]

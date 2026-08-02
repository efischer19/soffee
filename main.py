"""
SOFFEE - An OpenClaw skill for fantasy football league management.

This is the main entry point for the SOFFEE OpenClaw skill. Phase v0 is a
monolithic architecture that handles fantasy football queries, roster management,
and automated content generation via conversational AI in Slack.

For detailed information about the project, see: meta/SOFFEE.md
"""

import os
from difflib import get_close_matches
from typing import Any

from espn_api.football import League


def initialize_league() -> League | None:
    """
    Initialize and return an ESPN Fantasy Football League object.

    This function creates a League instance using credentials from environment
    variables. These credentials are required to access a private ESPN fantasy
    football league.

    Required environment variables:
    - ESPN_SWID: ESPN account ID (SWID cookie value)
    - ESPN_S2: ESPN session token (espn_s2 cookie value)
    - ESPN_LEAGUE_ID: ESPN fantasy league ID
    - ESPN_YEAR: League season year (e.g., 2024, 2025)

    Returns:
        League: An instantiated ESPN League object if all credentials are present.
        None: If any required credentials are missing.

    Example:
        >>> league = initialize_league()
        >>> if league:
        ...     print(f"Connected to league: {league.league_name}")
        ... else:
        ...     print("ESPN credentials not configured")
    """
    swid = os.environ.get("ESPN_SWID")
    s2 = os.environ.get("ESPN_S2")
    league_id = os.environ.get("ESPN_LEAGUE_ID")
    year = os.environ.get("ESPN_YEAR")

    # Validate that all required credentials are present
    if not all([swid, s2, league_id, year]):
        missing = [
            name
            for name, val in [
                ("ESPN_SWID", swid),
                ("ESPN_S2", s2),
                ("ESPN_LEAGUE_ID", league_id),
                ("ESPN_YEAR", year),
            ]
            if not val
        ]
        print(f"Missing ESPN credentials: {', '.join(missing)}")
        return None

    try:
        league = League(league_id=int(league_id), year=int(year), espn_s2=s2, swid=swid)
        return league
    except ValueError as e:
        print(f"Error: Invalid ESPN credentials format: {e}")
        return None
    except Exception as e:
        print(f"Error: Failed to initialize ESPN League: {e}")
        return None


def get_current_matchups(league: League | None) -> dict[str, Any]:
    """
    Retrieve the current week's matchups, live box scores, and projected points.

    This function queries the ESPN API using an initialized League object to
    retrieve the current week's matchups. It formats the raw API response into
    a clean, LLM-readable dictionary containing team names, current points, and
    projected points for each matchup.

    Args:
        league: An initialized ESPN League object. If None, returns error response.

    Returns:
        dict: A formatted response containing:
            - success (bool): Whether the operation succeeded
            - week (int): The current week number
            - matchups (list): List of matchup dictionaries, each containing:
                - matchup_id (int): Unique matchup identifier
                - home_team (str): Home team name
                - away_team (str): Away team name
                - home_score (float): Home team's current score
                - away_score (float): Away team's current score
                - home_projected (float): Home team's projected final score
                - away_projected (float): Away team's projected final score
            - error (str): Error message if operation failed

    Example:
        >>> league = initialize_league()
        >>> result = get_current_matchups(league)
        >>> if result['success']:
        ...     for matchup in result['matchups']:
        ...         print(f"{matchup['home_team']} vs {matchup['away_team']}")

    Raises:
        No exceptions are raised. All errors are caught and returned in the
        response dictionary with success=False and an error message.
    """
    if league is None:
        return {
            "success": False,
            "error": "League is None. Cannot fetch matchups.",
        }

    try:
        # Get current week from league
        current_week = league.current_week
        if current_week is None:
            return {
                "success": False,
                "error": "Unable to determine current week from league data.",
            }

        # Fetch box scores for current week
        box_scores = league.box_scores(week=current_week)
        if not box_scores:
            return {
                "success": True,
                "week": current_week,
                "matchups": [],
            }

        # Format matchups into LLM-readable format
        matchups = []
        for i, box_score in enumerate(box_scores):
            matchup = {
                "matchup_id": i,
                "home_team": box_score.home_team.team_name,
                "away_team": box_score.away_team.team_name,
                "home_score": round(box_score.home_score, 2),
                "away_score": round(box_score.away_score, 2),
                "home_projected": round(box_score.home_projected, 2),
                "away_projected": round(box_score.away_projected, 2),
            }
            matchups.append(matchup)

        return {
            "success": True,
            "week": current_week,
            "matchups": matchups,
        }

    except AttributeError as e:
        return {
            "success": False,
            "error": f"Invalid league data structure: {e}",
        }
    except (ConnectionError, TimeoutError) as e:
        return {
            "success": False,
            "error": f"API connection error: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error fetching matchups: {e}",
        }


def get_team_roster(league: League | None, team_name: str) -> dict[str, Any]:
    """
    Retrieve a team's active roster with player positions and injury statuses.

    This function queries the ESPN League object to find a team by name and
    retrieves its roster. It supports fuzzy matching to handle team names that
    don't exactly match the ESPN database. For each player on the roster, it
    returns their name, position, and current injury status.

    Args:
        league: An initialized ESPN League object. If None, returns error response.
        team_name: The name of the team to retrieve the roster for. Supports
                   partial name matching and case-insensitive search.

    Returns:
        dict: A formatted response containing:
            - success (bool): Whether the operation succeeded
            - team_name (str): The matched team name from the league
            - roster (list): List of player dictionaries, each containing:
                - name (str): Player's full name
                - position (str): Player's position (e.g., "QB", "RB", "WR")
                - injury_status (str): Injury status or empty string if active
                  (e.g., "Out", "Day to Day", "Questionable", "")
            - error (str): Error message if operation failed

    Example:
        >>> league = initialize_league()
        >>> result = get_team_roster(league, "Kansas City")
        >>> if result['success']:
        ...     for player in result['roster']:
        ...         print(f"{player['name']} ({player['position']})")

    Raises:
        No exceptions are raised. All errors are caught and returned in the
        response dictionary with success=False and an error message.
    """
    if league is None:
        return {
            "success": False,
            "error": "League is None. Cannot fetch team roster.",
        }

    if not team_name or not isinstance(team_name, str):
        return {
            "success": False,
            "error": "Invalid team_name: must be a non-empty string.",
        }

    try:
        # Get all team names from the league
        available_teams = [team.team_name for team in league.teams]

        # Try exact match first (case-insensitive)
        team_obj = None
        for team in league.teams:
            if team.team_name.lower() == team_name.lower():
                team_obj = team
                break

        # If no exact match, use fuzzy matching
        if team_obj is None:
            matches = get_close_matches(team_name, available_teams, n=1, cutoff=0.6)
            if matches:
                matched_name = matches[0]
                for team in league.teams:
                    if team.team_name == matched_name:
                        team_obj = team
                        break
            else:
                teams_list = ", ".join(available_teams)
                error_msg = (
                    f"Team '{team_name}' not found. Available teams: {teams_list}"
                )
                return {
                    "success": False,
                    "error": error_msg,
                }

        # Build roster data
        roster = []
        for player in team_obj.roster:
            player_data = {
                "name": player.name,
                "position": player.position,
                "injury_status": player.injuryStatus or "",
            }
            roster.append(player_data)

        # Sort roster by position for consistency
        roster_sorted = sorted(roster, key=lambda p: (p["position"], p["name"]))

        return {
            "success": True,
            "team_name": team_obj.team_name,
            "roster": roster_sorted,
        }

    except AttributeError as e:
        return {
            "success": False,
            "error": f"Invalid league data structure: {e}",
        }
    except (ConnectionError, TimeoutError) as e:
        return {
            "success": False,
            "error": f"API connection error: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error fetching team roster: {e}",
        }


def main():
    """
    Main entry point for the SOFFEE OpenClaw skill.

    This function is called by the OpenClaw framework when the skill is invoked.
    The actual implementation will evolve through the phased roadmap:

    - Phase v0: Monolithic skill with ESPN API integration
    - Phase v1: Refactored into soffee-core and soffee-skill packages
    - Phase v2+: Multi-platform support with provider adapters
    """
    # TODO: Implement skill logic
    pass


if __name__ == "__main__":
    main()

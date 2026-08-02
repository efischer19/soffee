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

import requests
from espn_api.football import League
from espn_api.football.constant import POSITION_MAP

from authorization import verify_team_ownership


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


def generate_batch_score_summary(league: League | None) -> dict[str, Any]:
    """
    Generate a structured, plain-text summary of the entire league's scoreboard.

    This function retrieves all current matchups for the week and formats them
    into a clean, non-conversational plain-text summary. The summary is designed
    to provide raw, structured data that an LLM can use to generate conversational
    updates for automated Slack broadcasts.

    Args:
        league: An initialized ESPN League object. If None, returns error response.

    Returns:
        dict: A formatted response containing:
            - success (bool): Whether the operation succeeded
            - week (int): The current week number
            - summary (str): Plain-text formatted summary of all matchups
            - error (str): Error message if operation failed

    Example:
        >>> league = initialize_league()
        >>> result = generate_batch_score_summary(league)
        >>> if result['success']:
        ...     print(result['summary'])

    The summary format is structured plain-text, not conversational:
        Week 5 Summary

        Matchup 1: Team A vs Team B
          Team A: 125.50 (Projected: 135.75)
          Team B: 118.25 (Projected: 130.00)

        Matchup 2: Team C vs Team D
          Team C: 120.00 (Projected: 130.00)
          Team D: 115.50 (Projected: 125.00)
    """
    # Get current matchups
    matchups_response = get_current_matchups(league)

    if not matchups_response["success"]:
        return {
            "success": False,
            "error": matchups_response.get("error", "Failed to retrieve matchups"),
        }

    week = matchups_response["week"]
    matchups = matchups_response["matchups"]

    # Build the summary
    summary_lines = [f"Week {week} Summary\n"]

    if not matchups:
        summary_lines.append("No matchups found for this week.")
        return {
            "success": True,
            "week": week,
            "summary": "\n".join(summary_lines),
        }

    for i, matchup in enumerate(matchups, 1):
        home_team = matchup["home_team"]
        away_team = matchup["away_team"]
        home_score = matchup["home_score"]
        away_score = matchup["away_score"]
        home_projected = matchup["home_projected"]
        away_projected = matchup["away_projected"]

        summary_lines.append(f"\nMatchup {i}: {home_team} vs {away_team}")
        summary_lines.append(
            f"  {home_team}: {home_score} (Projected: {home_projected})"
        )
        summary_lines.append(
            f"  {away_team}: {away_score} (Projected: {away_projected})"
        )

    return {
        "success": True,
        "week": week,
        "summary": "\n".join(summary_lines),
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


def set_lineup_status(
    league: League | None,
    slack_user_id: str,
    team_id: int,
    player_name: str,
    target_slot: str,
) -> dict[str, Any]:
    """
    Move a player to a specific lineup slot (starting or bench).

    This function updates a player's position in the fantasy football lineup by
    calling ESPN's write API endpoint. It supports moving players between starting
    positions and the bench.

    Args:
        league: An initialized ESPN League object. If None, returns error response.
        slack_user_id: The Slack User ID of the requesting user. Used for authorization
                      validation to ensure the user owns the team being modified.
        team_id: The ID of the team to update.
        player_name: The full name of the player to move. Supports fuzzy matching.
        target_slot: The target slot position (e.g., "QB", "RB", "WR", "BENCH", "IR").
                     Position names should be uppercase.

    Returns:
        dict: A formatted response containing:
            - success (bool): Whether the operation succeeded
            - player_name (str): The player that was moved (if successful)
            - previous_slot (str): The player's previous slot position
            - new_slot (str): The player's new slot position
            - error (str): Error message if operation failed

    Example:
        >>> league = initialize_league()
        >>> result = set_lineup_status(
        ...     league, "U1234567890", 1, "Patrick Mahomes", "BENCH"
        ... )
        >>> if result['success']:
        ...     player = result['player_name']
        ...     prev = result['previous_slot']
        ...     new = result['new_slot']
        ...     print(f"Moved {player} from {prev} to {new}")

    Raises:
        No exceptions are raised. All errors are caught and returned in the
        response dictionary with success=False and an error message.
    """
    # Verify authorization: ensure the user owns the team they're trying to modify
    if not verify_team_ownership(slack_user_id, team_id):
        return {
            "success": False,
            "error": (
                f"Unauthorized: Slack user {slack_user_id} does not own team {team_id}"
            ),
        }

    if league is None:
        return {
            "success": False,
            "error": "League is None. Cannot update lineup.",
        }

    if not player_name or not isinstance(player_name, str):
        return {
            "success": False,
            "error": "Invalid player_name: must be a non-empty string.",
        }

    if not target_slot or not isinstance(target_slot, str):
        return {
            "success": False,
            "error": "Invalid target_slot: must be a non-empty string.",
        }

    try:
        # Get the team
        team = None
        for t in league.teams:
            if t.team_id == team_id:
                team = t
                break

        if team is None:
            return {
                "success": False,
                "error": f"Team with ID {team_id} not found in league.",
            }

        # Find the player in the team's roster
        target_player = None
        available_players = [p.name for p in team.roster]

        # Try exact match first (case-insensitive)
        for player in team.roster:
            if player.name.lower() == player_name.lower():
                target_player = player
                break

        # If no exact match, use fuzzy matching
        if target_player is None:
            matches = get_close_matches(player_name, available_players, n=1, cutoff=0.6)
            if matches:
                matched_name = matches[0]
                for player in team.roster:
                    if player.name == matched_name:
                        target_player = player
                        break
            else:
                players_list = ", ".join(available_players)
                return {
                    "success": False,
                    "error": (
                        f"Player '{player_name}' not found on team. "
                        f"Available players: {players_list}"
                    ),
                }

        # Convert target_slot to slot ID
        target_slot_upper = target_slot.upper()

        # Special handling for BENCH and IR
        if target_slot_upper == "BENCH":
            target_slot_id = 20  # Bench slot
        elif target_slot_upper == "IR":
            target_slot_id = 21  # Injured Reserve slot
        elif target_slot_upper not in POSITION_MAP:
            valid_slots = ", ".join(
                sorted([k for k in POSITION_MAP if isinstance(k, str)])
            )
            return {
                "success": False,
                "error": (
                    f"Invalid slot '{target_slot}'. Valid slots: "
                    f"{valid_slots}, BENCH, IR"
                ),
            }
        else:
            target_slot_id = POSITION_MAP[target_slot_upper]

        previous_slot_id = target_player.slot_position
        previous_slot = None

        # Find the string representation of the previous slot
        for slot_id, _position in POSITION_MAP.items():
            if (
                isinstance(slot_id, str)
                and POSITION_MAP.get(slot_id) == previous_slot_id
            ):
                previous_slot = slot_id
                break
        if previous_slot is None:
            previous_slot = previous_slot_id

        # Build the roster entries for the PUT request
        # We need to send all players with their current slots, but update
        # the target player
        roster_entries = []
        for player in team.roster:
            if player.player_id == target_player.player_id:
                # This is the player we're moving - use the new slot
                entry = {
                    "playerId": player.player_id,
                    "slotId": target_slot_id,
                }
            else:
                # Keep other players in their current slots
                entry = {
                    "playerId": player.player_id,
                    "slotId": player.slot_position,
                }
            roster_entries.append(entry)

        # Prepare the request body
        payload = {
            "roster": {"entries": roster_entries},
            "scoringPeriodId": league.current_week,
        }

        # Build the endpoint URL - use lm-api for write operations
        endpoint = (
            f"https://lm-api.fantasy.espn.com/apis/v3/games/ffl/"
            f"seasons/{league.year}/segments/0/leagues/{league.league_id}/"
            f"teams/{team_id}"
        )

        # Make the PUT request with the league's cookies
        headers = {
            "Content-Type": "application/json",
            "x-fantasy-source": "kona",
        }

        # Get cookies from the league object
        cookies = None
        if hasattr(league, "espn_request") and hasattr(league.espn_request, "cookies"):
            cookies = league.espn_request.cookies

        response = requests.put(
            endpoint, json=payload, headers=headers, cookies=cookies, timeout=10
        )

        # Check response status
        if response.status_code == 200:
            return {
                "success": True,
                "player_name": target_player.name,
                "previous_slot": previous_slot,
                "new_slot": target_slot_upper,
            }
        elif response.status_code == 401:
            return {
                "success": False,
                "error": "Authentication failed. Check your ESPN credentials.",
            }
        elif response.status_code == 403:
            # This might be a "player locked" error or permissions issue
            error_msg = response.text if response.text else "Access denied"
            return {
                "success": False,
                "error": (
                    f"Cannot update lineup: {error_msg}. Player may be locked "
                    "or your account may not have permission."
                ),
            }
        else:
            return {
                "success": False,
                "error": f"ESPN API returned status {response.status_code}: "
                f"{response.text}",
            }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request to ESPN API timed out. Please try again.",
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "error": f"Connection error when contacting ESPN API: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error updating lineup: {e}",
        }


def process_waiver_transaction(
    league: League | None,
    slack_user_id: str,
    team_id: int,
    player_to_add: str,
    player_to_drop: str | None,
    bid_amount: int,
) -> dict[str, Any]:
    """
    Process a waiver wire claim or free agent addition transaction.

    This function executes an add/drop or waiver claim via the ESPN Fantasy
    Football API. It supports both free agent pickups and FAAB waiver claims
    (depending on league settings).

    Args:
        league: An initialized ESPN League object. If None, returns error response.
        slack_user_id: The Slack User ID of the requesting user. Used for
                      authorization validation to ensure the user owns the team
                      making the transaction.
        team_id: The ID of the team processing the transaction.
        player_to_add: The full name of the player to add. Supports fuzzy matching.
        player_to_drop: The full name of the player to drop, or None for free agent
                       pickup. Supports fuzzy matching.
        bid_amount: The FAAB bid amount (in currency units, typically $1-999).
                   Must be a positive integer.

    Returns:
        dict: A formatted response containing:
            - success (bool): Whether the transaction succeeded
            - transaction_type (str): Type of transaction ("WAIVER" or "FREEAGENT")
            - team_id (int): The team ID that made the transaction
            - player_added (str): Name of the player added
            - player_dropped (str): Name of the player dropped (if any)
            - bid_amount (int): The FAAB bid used
            - error (str): Error message if operation failed

    Example:
        >>> league = initialize_league()
        >>> result = process_waiver_transaction(
        ...     league, "U1234567890", 1, "Patrick Mahomes", "Backup QB", 5
        ... )
        >>> if result['success']:
        ...     print(f"Added {result['player_added']}")

    Raises:
        No exceptions are raised. All errors are caught and returned in the
        response dictionary with success=False and an error message.
    """
    # Verify authorization: ensure the user owns the team they're trying to modify
    if not verify_team_ownership(slack_user_id, team_id):
        return {
            "success": False,
            "error": (
                f"Unauthorized: Slack user {slack_user_id} does not own team {team_id}"
            ),
        }

    if league is None:
        return {
            "success": False,
            "error": "League is None. Cannot process transaction.",
        }

    # Validate team_id
    if not isinstance(team_id, int) or team_id <= 0:
        return {
            "success": False,
            "error": "Invalid team_id: must be a positive integer.",
        }

    # Validate player_to_add
    if not player_to_add or not isinstance(player_to_add, str):
        return {
            "success": False,
            "error": "Invalid player_to_add: must be a non-empty string.",
        }

    # Validate player_to_drop (can be None)
    if player_to_drop is not None and not isinstance(player_to_drop, str):
        return {
            "success": False,
            "error": "Invalid player_to_drop: must be a string or None.",
        }

    # Validate bid_amount
    if not isinstance(bid_amount, int) or bid_amount < 0:
        return {
            "success": False,
            "error": "Invalid bid_amount: must be a non-negative integer.",
        }

    if bid_amount > 999:
        return {
            "success": False,
            "error": "Invalid bid_amount: must not exceed 999.",
        }

    try:
        # Get the team
        team = None
        for t in league.teams:
            if t.team_id == team_id:
                team = t
                break

        if team is None:
            return {
                "success": False,
                "error": f"Team with ID {team_id} not found in league.",
            }

        # Find the player to add from all available players in the league
        # This includes players not on any roster (free agents) and potentially
        # players on other rosters (for trade/waiver scenarios)
        add_player = None
        add_player_id = None

        # Search through all league players (requires access to full player list)
        # First, try to find the player in free agents by getting all players
        try:
            # Use league's player list if available
            if hasattr(league, "players"):
                available_players = league.players
            else:
                # Fallback: search through all teams to build player list
                available_players = []
                for t in league.teams:
                    available_players.extend(t.roster)

            # Get list of player names for fuzzy matching
            player_names = [p.name for p in available_players]

            # Try exact match first (case-insensitive)
            for player in available_players:
                if player.name.lower() == player_to_add.lower():
                    add_player = player
                    add_player_id = player.player_id
                    break

            # If no exact match, use fuzzy matching
            if add_player_id is None:
                matches = get_close_matches(
                    player_to_add, player_names, n=1, cutoff=0.6
                )
                if matches:
                    matched_name = matches[0]
                    for player in available_players:
                        if player.name == matched_name:
                            add_player = player
                            add_player_id = player.player_id
                            break
                else:
                    return {
                        "success": False,
                        "error": f"Player '{player_to_add}' not found in league.",
                    }
        except (AttributeError, TypeError) as e:
            return {
                "success": False,
                "error": f"Unable to search for player: {e}",
            }

        # Check if player is already on this team
        for player in team.roster:
            if player.player_id == add_player_id:
                return {
                    "success": False,
                    "error": (
                        f"Player '{add_player.name}' is already on "
                        f"{team.team_name}'s roster."
                    ),
                }

        # Find the player to drop from the team's roster (if specified)
        drop_player = None
        drop_player_id = None

        if player_to_drop:
            team_player_names = [p.name for p in team.roster]

            # Try exact match first (case-insensitive)
            for player in team.roster:
                if player.name.lower() == player_to_drop.lower():
                    drop_player = player
                    drop_player_id = player.player_id
                    break

            # If no exact match, use fuzzy matching
            if drop_player_id is None:
                matches = get_close_matches(
                    player_to_drop, team_player_names, n=1, cutoff=0.6
                )
                if matches:
                    matched_name = matches[0]
                    for player in team.roster:
                        if player.name == matched_name:
                            drop_player = player
                            drop_player_id = player.player_id
                            break
                else:
                    return {
                        "success": False,
                        "error": (
                            f"Player '{player_to_drop}' not found on "
                            f"{team.team_name}'s roster."
                        ),
                    }

        # Determine transaction type based on bid_amount
        # If bid_amount is 0 and there's a drop, or no drop, it's a free agent pickup
        # If bid_amount > 0, it's a waiver claim (FAAB)
        transaction_type = "WAIVER" if bid_amount > 0 else "FREEAGENT"

        # Build the transaction payload
        payload = {
            "transactions": [
                {
                    "type": transaction_type,
                    "tradedPlayers": [],
                    "addedPlayerIds": [add_player_id],
                    "droppedPlayerIds": [drop_player_id] if drop_player_id else [],
                    "bidAmount": bid_amount,
                }
            ]
        }

        # Build the endpoint URL
        endpoint = (
            f"https://lm-api.fantasy.espn.com/apis/v3/games/ffl/"
            f"seasons/{league.year}/segments/0/leagues/{league.league_id}/"
            f"transactions"
        )

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "x-fantasy-source": "kona",
        }

        # Get cookies from the league object
        cookies = None
        if hasattr(league, "espn_request") and hasattr(league.espn_request, "cookies"):
            cookies = league.espn_request.cookies

        # Make the POST request
        response = requests.post(
            endpoint, json=payload, headers=headers, cookies=cookies, timeout=10
        )

        # Check response status
        if response.status_code == 200:
            return {
                "success": True,
                "transaction_type": transaction_type,
                "team_id": team_id,
                "player_added": add_player.name,
                "player_dropped": drop_player.name if drop_player else None,
                "bid_amount": bid_amount,
            }
        elif response.status_code == 401:
            return {
                "success": False,
                "error": "Authentication failed. Check your ESPN credentials.",
            }
        elif response.status_code == 403:
            error_msg = response.text if response.text else "Access denied"
            return {
                "success": False,
                "error": f"Permission denied: {error_msg}",
            }
        else:
            return {
                "success": False,
                "error": f"ESPN API returned status {response.status_code}: "
                f"{response.text}",
            }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request to ESPN API timed out. Please try again.",
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "error": f"Connection error when contacting ESPN API: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error processing transaction: {e}",
        }


def detect_roster_violations(league: League | None, week: int) -> dict[str, Any]:
    """
    Detect starting roster violations for a given week.

    This function sweeps all team rosters for a specific week and identifies any
    starting players who are either on a bye week or officially marked as "OUT"
    or "IR" due to injury. Only active starting lineup slots are checked; bench
    and IR slots are ignored.

    Args:
        league: An initialized ESPN League object. If None, returns error response.
        week: The fantasy week number to check (1-17 for regular season).

    Returns:
        dict: A formatted response containing:
            - success (bool): Whether the operation succeeded
            - week (int): The week that was checked
            - violations (dict): Dictionary mapping team_id to list of violating
              players. Each player violation contains:
                - name (str): Player's full name
                - position (str): Player's position (e.g., "QB", "RB", "WR")
                - violation_reason (str): Reason for violation ("bye" or injury
                  status string like "Out", "Questionable", etc.)
            - error (str): Error message if operation failed

    Example:
        >>> league = initialize_league()
        >>> result = detect_roster_violations(league, 5)
        >>> if result['success']:
        ...     for team_id, players in result['violations'].items():
        ...         print(f"Team {team_id}: {len(players)} violations")

    Raises:
        No exceptions are raised. All errors are caught and returned in the
        response dictionary with success=False and an error message.
    """
    if league is None:
        return {
            "success": False,
            "error": "League is None. Cannot detect roster violations.",
        }

    if not isinstance(week, int) or week < 1 or week > 17:
        return {
            "success": False,
            "error": "Invalid week: must be an integer between 1 and 17.",
        }

    try:
        # Load the roster for the specific week
        league.load_roster_week(week)

        violations = {}

        # Iterate through all teams
        for team in league.teams:
            team_violations = []

            # Check each player in the team's roster
            for player in team.roster:
                # Skip bench and IR slots - only check starting positions
                if player.lineupSlot in ("BE", "IR", ""):
                    continue

                # Check if player is on bye week
                if player.active_status == "bye":
                    team_violations.append(
                        {
                            "name": player.name,
                            "position": player.position,
                            "violation_reason": "bye",
                        }
                    )
                    continue

                # Check if player has OUT or IR injury status
                if player.injuryStatus and player.injuryStatus.upper() in (
                    "OUT",
                    "IR",
                ):
                    team_violations.append(
                        {
                            "name": player.name,
                            "position": player.position,
                            "violation_reason": player.injuryStatus,
                        }
                    )

            # Only add to violations if there are any for this team
            if team_violations:
                violations[team.team_id] = team_violations

        return {
            "success": True,
            "week": week,
            "violations": violations,
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
            "error": f"Unexpected error detecting roster violations: {e}",
        }


def get_top_free_agent_replacements(
    league: League | None, position: str, week: int, limit: int = 3
) -> dict[str, Any]:
    """
    Retrieve the top available free agents for a position sorted by projection.

    This function queries the ESPN League to find available free agents at a
    specific position, filters them by projected points for a given week, and
    returns the top players sorted by their projected fantasy points in
    descending order.

    Args:
        league: An initialized ESPN League object. If None, returns error response.
        position: The position to filter by (e.g., 'QB', 'RB', 'WR', 'TE', 'K', 'D/ST').
        week: The fantasy week number for which to retrieve projections (1-17 for
              regular season). Used to filter stats by scoringPeriodId.
        limit: Maximum number of free agents to return (default: 3).

    Returns:
        dict: A formatted response containing:
            - success (bool): Whether the operation succeeded
            - position (str): The position that was queried
            - week (int): The week for which projections were retrieved
            - players (list): List of top free agent dictionaries, sorted highest
                            to lowest by projected_points. Each player dict contains:
                - name (str): Player's full name
                - position (str): Player's position
                - pro_team (str): Player's NFL team abbreviation
                - projected_points (float): Projected fantasy points for the week
                - percent_owned (float): Percentage of league that owns the player
            - count (int): Number of players returned
            - error (str): Error message if operation failed

    Example:
        >>> league = initialize_league()
        >>> result = get_top_free_agent_replacements(league, 'RB', week=5, limit=3)
        >>> if result['success']:
        ...     for player in result['players']:
        ...         print(f"{player['name']}: {player['projected_points']} pts")

    Raises:
        No exceptions are raised. All errors are caught and returned in the
        response dictionary with success=False and an error message.
    """
    if league is None:
        return {
            "success": False,
            "error": "League is None. Cannot fetch free agents.",
        }

    if not position or not isinstance(position, str):
        return {
            "success": False,
            "error": "Invalid position: must be a non-empty string.",
        }

    if not isinstance(week, int) or week < 1:
        return {
            "success": False,
            "error": "Invalid week: must be a positive integer.",
        }

    if not isinstance(limit, int) or limit < 1:
        return {
            "success": False,
            "error": "Invalid limit: must be a positive integer.",
        }

    try:
        # Fetch free agents for the specified position
        free_agents = league.free_agents(position=position, week=week, size=100)

        # Build list of players with projected points
        players_with_projections = []
        for player in free_agents:
            # Access projected points for the specific week
            week_stats = player.stats.get(week, {})
            projected_points = week_stats.get("projected_points", 0)

            player_data = {
                "name": player.name,
                "position": player.position,
                "pro_team": player.proTeam or "",
                "projected_points": projected_points,
                "percent_owned": player.percent_owned or 0,
            }
            players_with_projections.append(player_data)

        # Sort by projected_points descending
        sorted_players = sorted(
            players_with_projections,
            key=lambda p: p["projected_points"],
            reverse=True,
        )

        # Return top N players
        top_players = sorted_players[:limit]

        return {
            "success": True,
            "position": position,
            "week": week,
            "players": top_players,
            "count": len(top_players),
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
            "error": f"Unexpected error fetching free agents: {e}",
        }


def run_sunday_roster_sweep(league: League | None, week: int) -> dict[str, Any]:
    """
    Execute the Sunday morning automated roster violation sweep.

    This function detects starting roster violations (bye weeks and injuries),
    retrieves top free agent replacements for violating positions, and posts
    Slack messages to each affected manager with helpful suggestions and
    light-hearted banter about their roster management.

    The function implements the core workflow for the automated Sunday morning
    roster sweep cron job. It follows the principle of augmenting human
    interaction rather than replacing it—providing proactive suggestions while
    keeping managers engaged and entertained.

    Args:
        league: An initialized ESPN League object. If None, returns error response.
        week: The fantasy week number to check (1-17 for regular season).

    Returns:
        dict: A formatted response containing:
            - success (bool): Whether the operation succeeded
            - week (int): The week that was checked
            - violations_found (int): Number of teams with violations
            - messages_posted (int): Number of Slack messages posted
            - error (str): Error message if operation failed

    Example:
        >>> league = initialize_league()
        >>> result = run_sunday_roster_sweep(league, week=5)
        >>> if result['success']:
        ...     print(f"Found violations for {result['violations_found']} teams")
    """
    if league is None:
        return {
            "success": False,
            "error": "League is None. Cannot run roster sweep.",
        }

    if not isinstance(week, int) or week < 1 or week > 17:
        return {
            "success": False,
            "error": "Invalid week: must be an integer between 1 and 17.",
        }

    try:
        from authorization import get_slack_user_for_team

        # Step 1: Detect all roster violations
        violations_result = detect_roster_violations(league, week)

        if not violations_result.get("success"):
            return violations_result

        violations = violations_result.get("violations", {})

        if not violations:
            return {
                "success": True,
                "week": week,
                "violations_found": 0,
                "messages_posted": 0,
            }

        messages_posted = 0

        # Step 2: Process each team with violations
        for team_id, players in violations.items():
            # Get the Slack user for this team
            slack_user_id = get_slack_user_for_team(team_id)

            # Skip if we can't find a Slack user for this team
            if not slack_user_id:
                continue

            # Get team name for context
            team = None
            for t in league.teams:
                if t.team_id == team_id:
                    team = t
                    break

            team_name = team.team_name if team else f"Team {team_id}"

            # Collect unique positions from violations
            positions_with_violations = {}
            for player in players:
                position = player["position"]
                if position not in positions_with_violations:
                    positions_with_violations[position] = []
                positions_with_violations[position].append(player)

            # Step 3: Get free agent replacements for each violating position
            replacement_suggestions = {}
            for position, _violating_players in positions_with_violations.items():
                replacements_result = get_top_free_agent_replacements(
                    league, position, week, limit=3
                )

                if replacements_result.get("success"):
                    replacement_suggestions[position] = replacements_result.get(
                        "players", []
                    )

            # Step 4: Format and post Slack message
            message = _format_roster_sweep_message(
                slack_user_id, team_name, players, replacement_suggestions
            )

            if message:
                # Post to Slack using the OpenClaw framework
                try:
                    slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
                    if not slack_bot_token:
                        print(f"Warning: SLACK_BOT_TOKEN not set for team {team_id}")
                        continue

                    response = requests.post(
                        "https://slack.com/api/chat.postMessage",
                        headers={
                            "Authorization": "******",
                            "Content-Type": "application/json",
                        },
                        json={
                            "channel": slack_user_id,  # Direct message to the user
                            "text": message,
                        },
                    )

                    if response.status_code == 200:
                        messages_posted += 1
                except Exception as e:
                    # Log the error but continue processing other teams
                    print(f"Failed to post Slack message for team {team_id}: {e}")

        return {
            "success": True,
            "week": week,
            "violations_found": len(violations),
            "messages_posted": messages_posted,
        }

    except (AttributeError, ConnectionError, TimeoutError) as e:
        return {
            "success": False,
            "error": f"Error during roster sweep: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error during roster sweep: {e}",
        }


def _format_roster_sweep_message(
    slack_user_id: str, team_name: str, violations: list, suggestions: dict
) -> str:
    """
    Format a roster violation message for Slack posting.

    Constructs an engaging message that highlights roster violations while
    providing helpful suggestions for free agent replacements. The message
    includes light banter about the manager's roster management per the
    project's engagement philosophy.

    Args:
        slack_user_id: The Slack User ID to tag in the message.
        team_name: The name of the team with violations.
        violations: List of player violation dicts from detect_roster_violations().
        suggestions: Dictionary mapping positions to lists of suggested free agents.

    Returns:
        str: A formatted Slack message ready for posting.
    """
    lines = []

    # Header with tag and light banter
    lines.append(f"<@{slack_user_id}> 🚨 Your roster needs some love!")
    lines.append(
        f"_Team: {team_name}_ — We found some rough decisions you made this week:"
    )
    lines.append("")

    # List violations by position
    for violation in violations:
        name = violation.get("name", "Unknown Player")
        position = violation.get("position", "?")
        reason = violation.get("violation_reason", "unknown reason")

        reason_text = (
            "bye week" if reason.lower() == "bye" else f"{reason.lower()} status"
        )
        lines.append(f"❌ **{name}** ({position}) — {reason_text}")

    lines.append("")

    # Suggest replacements
    lines.append("_Here are some free agent pickups to save you:_")

    if suggestions:
        for position, players in suggestions.items():
            if players:
                lines.append(f"\n**{position} Options:**")
                for i, player in enumerate(players[:3], 1):
                    name = player.get("name", "Unknown")
                    proj_pts = player.get("projected_points", 0)
                    pro_team = player.get("pro_team", "?")
                    lines.append(
                        f"{i}. {name} ({pro_team}) — {proj_pts:.1f} pts projected"
                    )
    else:
        lines.append("_No free agent suggestions available for these positions._")

    lines.append("")
    lines.append("💬 React with 👍 to confirm, or reply with your preferred picks!")

    return "\n".join(lines)


def get_historical_season(year: int) -> dict[str, Any]:
    """
    Retrieve historical season data for a given year.

    This function instantiates a League object for a specified historical year
    and extracts the final standings with total points for and against. It uses
    the same ESPN credentials (ESPN_SWID, ESPN_S2, ESPN_LEAGUE_ID) that are
    configured for the current season.

    Args:
        year: The season year to retrieve historical data for (e.g., 2024, 2025).

    Returns:
        dict: A formatted response containing:
            - success (bool): Whether the operation succeeded
            - year (int): The requested season year
            - league_name (str): Name of the league
            - standings (list): List of team standings, each containing:
                - team_name (str): Name of the team
                - team_id (int): ESPN team ID
                - wins (int): Number of wins for the season
                - losses (int): Number of losses for the season
                - points_for (float): Total points scored by the team
                - points_against (float): Total points scored against the team
            - error (str): Error message if operation failed

    Example:
        >>> result = get_historical_season(2024)
        >>> if result['success']:
        ...     for team in result['standings']:
        ...         print(f"{team['team_name']}: {team['wins']}-{team['losses']}")

    Raises:
        No exceptions are raised. All errors are caught and returned in the
        response dictionary with success=False and an error message.
    """
    swid = os.environ.get("ESPN_SWID")
    s2 = os.environ.get("ESPN_S2")
    league_id = os.environ.get("ESPN_LEAGUE_ID")

    # Validate that required credentials are present
    if not all([swid, s2, league_id]):
        missing = [
            name
            for name, val in [
                ("ESPN_SWID", swid),
                ("ESPN_S2", s2),
                ("ESPN_LEAGUE_ID", league_id),
            ]
            if not val
        ]
        missing_creds = ", ".join(missing)
        error_msg = (
            f"Missing ESPN credentials required for historical data retrieval: "
            f"{missing_creds}"
        )
        return {
            "success": False,
            "year": year,
            "error": error_msg,
        }

    try:
        # Attempt to instantiate League object for the specified year
        league = League(
            league_id=int(league_id), year=int(year), espn_s2=s2, swid=swid
        )

        # Extract standings data
        standings_data = []
        if league.standings:
            for team in league.standings:
                standings_data.append(
                    {
                        "team_name": team.team_name,
                        "team_id": team.team_id,
                        "wins": team.wins,
                        "losses": team.losses,
                        "points_for": round(team.points_for, 2),
                        "points_against": round(team.points_against, 2),
                    }
                )

        return {
            "success": True,
            "year": year,
            "league_name": league.league_name,
            "standings": standings_data,
        }

    except ValueError as e:
        return {
            "success": False,
            "year": year,
            "error": f"Invalid ESPN credentials format or year value: {e}",
        }
    except KeyError as e:
        error_msg = (
            f"The requested year {year} may not exist for this league. "
            f"Please verify the year is within the league's history: {e}"
        )
        return {
            "success": False,
            "year": year,
            "error": error_msg,
        }
    except (ConnectionError, TimeoutError) as e:
        return {
            "success": False,
            "year": year,
            "error": f"Failed to connect to ESPN API: {e}",
        }
    except Exception as e:
        error_msg = (
            f"Unexpected error retrieving historical season data for {year}: {e}"
        )
        return {
            "success": False,
            "year": year,
            "error": error_msg,
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

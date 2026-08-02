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

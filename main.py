"""
SOFFEE - An OpenClaw MCP Tool for fantasy football league management.

This is the read-only entry point for the SOFFEE OpenClaw tool (Phase v0).
It handles fantasy football queries, roster checks, and historical data retrieval
using the Model Context Protocol (MCP).
"""

import json
import os
import sys
import time
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from typing import Any

from espn_api.football import League
from mcp.server.fastmcp import FastMCP

ENV_FILE = Path(__file__).resolve().parent / ".env"
REQUIRED_ENV = ("ESPN_SWID", "ESPN_S2", "ESPN_LEAGUE_ID", "ESPN_YEAR")
CURRENT_SEASON_TTL = 300  # seconds; live scores change, so refetch every few minutes
PAST_SEASON_TTL = 24 * 3600  # finished seasons don't change


def load_env_file(path: Path = ENV_FILE) -> None:
    """Load KEY=VALUE lines from the .env next to this file. Variables already set in the environment win."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)


load_env_file()

# Initialize the MCP server
mcp = FastMCP("SOFFEE Fantasy Football")


@dataclass(frozen=True)
class LeagueInitializationError:
    error: str


LeagueContext = League | LeagueInitializationError | None

_league_cache: dict[int, tuple] = {}  # year -> (fetched_at, League)


def _league_unavailable_response(
    league: LeagueContext, default_message: str
) -> dict[str, Any] | None:
    if isinstance(league, LeagueInitializationError):
        return {"success": False, "error": league.error}
    if league is None:
        return {"success": False, "error": default_message}
    return None


def initialize_league(
    year: int | None = None, fresh: bool = False
) -> League | LeagueInitializationError:
    """Return the ESPN League for `year` (default: ESPN_YEAR), reusing a recent fetch instead of hitting ESPN every call.

    Pass fresh=True for callers that mutate the League (e.g. load_roster_week), so they don't alter the shared copy.
    """
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        return LeagueInitializationError(
            f"Missing settings {missing}; add them to {ENV_FILE}."
        )

    current_year = int(os.environ["ESPN_YEAR"])
    year = int(year or current_year)
    ttl = CURRENT_SEASON_TTL if year >= current_year else PAST_SEASON_TTL
    cached = _league_cache.get(year)
    if cached and not fresh and time.time() - cached[0] < ttl:
        return cached[1]

    try:
        league = League(
            league_id=int(os.environ["ESPN_LEAGUE_ID"]),
            year=year,
            espn_s2=os.environ["ESPN_S2"],
            swid=os.environ["ESPN_SWID"],
        )
    except Exception as e:
        return LeagueInitializationError(f"Failed to initialize ESPN League: {e}")
    if not fresh:
        _league_cache[year] = (time.time(), league)
    return league


@mcp.tool()
def get_scoreboard(week: int | None = None) -> dict[str, Any]:
    """
    AGENT INSTRUCTION: Use this tool for a HIGH-LEVEL overview of team vs. team scores and matchup outcomes.
    Do NOT use this if you need player-level statistics, projections, or roster details.

    Retrieves the team-level scoreboard for a given week (defaults to the current week if none provided).
    """
    league = initialize_league()
    unavailable = _league_unavailable_response(league, "League unavailable.")
    if unavailable:
        return unavailable

    try:
        target_week = week or league.current_week
        if target_week >= league.current_week:
            # scoreboard() reads ESPN's settled `totalPoints`, which stays 0 until the week is final.
            # box_scores() reads `totalPointsLive`, so in-progress weeks show real scores.
            results = [
                {
                    "home_team": bs.home_team.team_name if bs.home_team else "Unknown",
                    "away_team": bs.away_team.team_name if bs.away_team else "Unknown",
                    "home_score": round(bs.home_score, 2),
                    "away_score": round(bs.away_score, 2),
                    "home_projected": round(bs.home_projected, 2),
                    "away_projected": round(bs.away_projected, 2),
                }
                for bs in league.box_scores(week=target_week)
            ]
            return {
                "success": True,
                "week": target_week,
                "live": True,
                "matchups": results,
            }

        matchups = league.scoreboard(week=target_week)

        results = [
            {
                "home_team": m.home_team.team_name if m.home_team else "Unknown",
                "away_team": m.away_team.team_name if m.away_team else "Unknown",
                "home_score": round(m.home_score, 2),
                "away_score": round(m.away_score, 2),
            }
            for m in matchups
        ]
        return {"success": True, "week": target_week, "matchups": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_box_scores(
    week: int | None = None,
    team_name: str | None = None,
    include_bench: bool = False,
) -> dict[str, Any]:
    """
    AGENT INSTRUCTION: Use this tool ONLY when you need GRANULAR player-level statistics and lineup information.
    For team scores AND team projections, use `get_scoreboard` instead — it is much smaller.
    Pass `team_name` to get just that team's matchup. Bench/IR players are left out unless `include_bench` is true.

    Retrieves detailed box scores and projections for a given week (defaults to current week).
    """
    league = initialize_league()
    unavailable = _league_unavailable_response(league, "League unavailable.")
    if unavailable:
        return unavailable

    try:
        target_week = week or league.current_week
        box_scores = league.box_scores(week=target_week)

        def lineup(players):
            return [
                f"{p.slot_position} {p.name} — {round(p.points, 2)} pts (proj {round(p.projected_points, 2)}) [id {p.playerId}]"
                for p in players
                if include_bench or p.slot_position not in ("BE", "IR")
            ]

        needle = team_name.lower() if team_name else None
        matchups = []
        for bs in box_scores:
            names = (bs.home_team.team_name, bs.away_team.team_name)
            if needle and not any(needle in n.lower() for n in names):
                continue
            matchups.append(
                {
                    "home_team": names[0],
                    "away_team": names[1],
                    "home_score": round(bs.home_score, 2),
                    "away_score": round(bs.away_score, 2),
                    "home_projected": round(bs.home_projected, 2),
                    "away_projected": round(bs.away_projected, 2),
                    "home_lineup": lineup(bs.home_lineup),
                    "away_lineup": lineup(bs.away_lineup),
                }
            )

        if needle and not matchups:
            return {
                "success": False,
                "error": f"No matchup found for team '{team_name}' in week {target_week}.",
            }
        return {"success": True, "week": target_week, "box_scores": matchups}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_pro_schedule(week: int | None = None) -> dict[str, Any]:
    """
    Retrieves the real-life (IRL) NFL schedule for the given fantasy week.
    Use this to determine game dates/times and whether real-life games have occurred yet.
    """
    league = initialize_league()
    unavailable = _league_unavailable_response(league, "League unavailable.")
    if unavailable:
        return unavailable

    try:
        target_week = week or league.current_week
        schedule_data = league._get_pro_schedule(scoringPeriodId=target_week)

        formatted_schedule = {
            pro_team_id: {"opponent_id": data[0], "date_ms": data[1]}
            for pro_team_id, data in schedule_data.items()
        }
        return {"success": True, "week": target_week, "schedule": formatted_schedule}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_standings(week: int | None = None) -> dict[str, Any]:
    """
    Retrieves the league standings. If a week is provided, it returns the standings exactly as they were up to that week.
    """
    league = initialize_league()
    unavailable = _league_unavailable_response(league, "League unavailable.")
    if unavailable:
        return unavailable

    try:
        if week and week < league.current_week:
            standings_obj = league.standings_weekly(week=week)
        else:
            standings_obj = league.standings()

        standings = [
            {
                "rank": idx + 1,
                "team_name": t.team_name,
                "wins": t.wins,
                "losses": t.losses,
                "ties": t.ties,
                "points_for": round(t.points_for, 2),
                "points_against": round(t.points_against, 2),
            }
            for idx, t in enumerate(standings_obj)
        ]
        return {
            "success": True,
            "week": week or league.current_week,
            "standings": standings,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_power_rankings(week: int | None = None) -> dict[str, Any]:
    """
    Retrieves the league's power rankings for a given week.
    This utilizes two-step dominance matrices based on win/loss margins.
    """
    league = initialize_league()
    unavailable = _league_unavailable_response(league, "League unavailable.")
    if unavailable:
        return unavailable

    try:
        rankings = league.power_rankings(week=week)
        formatted_rankings = [
            {
                "rank": idx + 1,
                "team_name": t[1].team_name,
                "power_score": round(float(t[0]), 2),
            }
            for idx, t in enumerate(rankings)
        ]
        return {
            "success": True,
            "week": week or league.current_week,
            "power_rankings": formatted_rankings,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_recent_activity(size: int = 15) -> dict[str, Any]:
    """
    Retrieves the most recent league activity including waiver wire adds, drops, and trades.
    """
    league = initialize_league()
    unavailable = _league_unavailable_response(league, "League unavailable.")
    if unavailable:
        return unavailable

    try:
        activities = league.recent_activity(size=size)
        results = []
        for act in activities:
            # espn_api yields (team, action, player, bid_amount); team may be ''/None and player may be a bare id.
            details = []
            for team, action, player, *rest in act.actions:
                team_name = getattr(team, "team_name", None) or "Unknown team"
                player_name = getattr(player, "name", None) or str(player)
                bid = rest[0] if rest else 0
                details.append(
                    f"{team_name} {action} {player_name}"
                    + (f" (${bid})" if bid else "")
                )
            results.append(
                {
                    "type": act.actions[0][1] if act.actions else "Unknown",
                    "date": act.date,
                    "details": details,
                }
            )
        return {"success": True, "activity": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_player_info(
    player_name: str | None = None, player_id: int | None = None
) -> dict[str, Any]:
    """
    AGENT INSTRUCTION: Drill down into a specific player to get their profile, real-life team,
    injury status, and recent news. If you know the player_id, use that instead of the name.
    """
    if not player_name and not player_id:
        return {
            "success": False,
            "error": "Must provide either player_name or player_id.",
        }

    league = initialize_league()
    unavailable = _league_unavailable_response(league, "League unavailable.")
    if unavailable:
        return unavailable

    try:
        target_id = player_id
        if not target_id and player_name:
            target_id = league.player_map.get(player_name)
            if not target_id:
                return {
                    "success": False,
                    "error": f"Player '{player_name}' not found in league map.",
                }

        player = league.player_info(playerId=target_id)
        if not player:
            return {"success": False, "error": "Player data not found."}

        if isinstance(player, list):
            player = player[0]

        info = {
            "player_id": target_id,
            "name": player.name,
            "position": player.position,
            "pro_team": player.proTeam,
            "injury_status": player.injuryStatus,
            "percent_owned": round(player.percent_owned, 2)
            if getattr(player, "percent_owned", None)
            else 0.0,
        }

        try:
            raw_news = league.espn_request.get_player_news(target_id)
            # ESPN typically nests the news items in an 'articles' or 'news' array.
            # We will safely grab just the first 3 recent blurbs.
            articles = raw_news.get("articles", [])[:3]

            parsed_news = [
                {
                    "headline": article.get("headline", "No headline"),
                    "description": article.get("description", "No description"),
                }
                for article in articles
            ]
            info["news"] = parsed_news
        except Exception as e:
            info["news"] = {"error": f"News unavailable: {str(e)}"}

        return {"success": True, "player": info}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_team_roster(team_name: str) -> dict[str, Any]:
    """Retrieve a team's active roster with player positions and injury statuses."""
    league = initialize_league()
    unavailable = _league_unavailable_response(league, "League unavailable.")
    if unavailable:
        return unavailable

    try:
        available_teams = [t.team_name for t in league.teams]
        team_obj = next(
            (t for t in league.teams if t.team_name.lower() == team_name.lower()), None
        )

        if not team_obj:
            matches = get_close_matches(team_name, available_teams, n=1, cutoff=0.6)
            if matches:
                team_obj = next(
                    (t for t in league.teams if t.team_name == matches[0]), None
                )
            else:
                return {
                    "success": False,
                    "error": f"Team not found. Available: {', '.join(available_teams)}",
                }

        roster = [
            {
                "player_id": p.playerId,
                "name": p.name,
                "position": p.position,
                "injury_status": p.injuryStatus or "",
            }
            for p in team_obj.roster
        ]
        roster_sorted = sorted(roster, key=lambda p: (p["position"], p["name"]))
        return {
            "success": True,
            "team_name": team_obj.team_name,
            "roster": roster_sorted,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def detect_roster_violations(week: int) -> dict[str, Any]:
    """Detect starting roster violations (byes, OUT, IR) for a given week."""
    league = initialize_league(fresh=True)  # load_roster_week mutates the League
    unavailable = _league_unavailable_response(league, "League unavailable.")
    if unavailable:
        return unavailable

    try:
        league.load_roster_week(week)
        violations = {}

        for team in league.teams:
            team_violations = []
            for player in team.roster:
                if player.lineupSlot in ("BE", "IR", ""):
                    continue
                if player.active_status == "bye":
                    team_violations.append(
                        {
                            "player_id": player.playerId,
                            "name": player.name,
                            "position": player.position,
                            "violation_reason": "bye",
                        }
                    )
                elif player.injuryStatus and player.injuryStatus.upper() in (
                    "OUT",
                    "IR",
                ):
                    team_violations.append(
                        {
                            "player_id": player.playerId,
                            "name": player.name,
                            "position": player.position,
                            "violation_reason": player.injuryStatus,
                        }
                    )
            if team_violations:
                violations[team.team_id] = team_violations

        return {"success": True, "week": week, "violations": violations}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_top_free_agent_replacements(
    position: str, week: int, limit: int = 3
) -> dict[str, Any]:
    """Retrieve the top available free agents for a position sorted by projection."""
    league = initialize_league()
    unavailable = _league_unavailable_response(league, "League unavailable.")
    if unavailable:
        return unavailable

    try:
        free_agents = league.free_agents(position=position, week=week, size=100)
        players = [
            {
                "player_id": p.playerId,
                "name": p.name,
                "position": p.position,
                "pro_team": p.proTeam or "",
                "projected_points": p.stats.get(week, {}).get("projected_points", 0),
                "percent_owned": p.percent_owned or 0,
            }
            for p in free_agents
        ]
        top_players = sorted(
            players, key=lambda p: p["projected_points"], reverse=True
        )[:limit]
        return {
            "success": True,
            "position": position,
            "week": week,
            "players": top_players,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def generate_batch_score_summary() -> str:
    """Generate a structured, plain-text summary of the entire league's scoreboard."""
    matchups_response = get_scoreboard()
    if not matchups_response.get("success"):
        return f"Error: {matchups_response.get('error')}"

    week = matchups_response["week"]
    matchups = matchups_response["matchups"]
    summary_lines = [f"Week {week} Summary\n"]

    if not matchups:
        return "No matchups found for this week."

    for i, matchup in enumerate(matchups, 1):
        summary_lines.append(
            f"\nMatchup {i}: {matchup['home_team']} vs {matchup['away_team']}"
        )
        summary_lines.append(f"  {matchup['home_team']}: {matchup['home_score']}")
        summary_lines.append(f"  {matchup['away_team']}: {matchup['away_score']}")

    return "\n".join(summary_lines)


@mcp.tool()
def get_historical_season_summary(year: int) -> dict[str, Any]:
    """Retrieve historical season standings and scores for a given year."""
    league = initialize_league(year=year)
    unavailable = _league_unavailable_response(league, "League unavailable.")
    if unavailable:
        return unavailable

    try:
        standings = [
            {
                "team_name": t.team_name,
                "team_id": t.team_id,
                "wins": t.wins,
                "losses": t.losses,
                "points_for": round(t.points_for, 2),
                "points_against": round(t.points_against, 2),
            }
            for t in league.standings()
        ]
        return {
            "success": True,
            "year": year,
            "league_name": league.settings.name,
            "standings": standings,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_team_owners() -> dict[str, Any]:
    """
    Map Slack users to their fantasy teams. Use this to know whose team is whose; never guess ownership.
    Returns each Slack user ID with their team's name and ID.
    """
    raw = os.environ.get("SOFFEE_SLACK_USER_TO_TEAM_MAP")
    if not raw:
        return {
            "success": False,
            "error": "SOFFEE_SLACK_USER_TO_TEAM_MAP is not configured.",
        }
    try:
        slack_to_team_id = json.loads(raw)
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"SOFFEE_SLACK_USER_TO_TEAM_MAP is not valid JSON: {e}",
        }

    league = initialize_league()
    unavailable = _league_unavailable_response(league, "League unavailable.")
    if unavailable:
        return unavailable

    teams_by_id = {t.team_id: t.team_name for t in league.teams}
    owners = [
        {
            "slack_user_id": slack_id,
            "team_id": team_id,
            "team_name": teams_by_id.get(int(team_id), "Unknown team"),
        }
        for slack_id, team_id in slack_to_team_id.items()
    ]
    return {"success": True, "owners": owners}


def check() -> int:
    """Connect to ESPN once and report, so a broken setup shows up in seconds instead of as silently missing tools."""
    league = initialize_league()
    if isinstance(league, LeagueInitializationError):
        print(f"FAIL: {league.error}")
        return 1
    print(
        f"OK: '{league.settings.name}' {league.year}, week {league.current_week}, {len(league.teams)} teams"
    )
    owners = get_team_owners()
    print(
        f"Team owners map: {len(owners['owners'])} entries"
        if owners["success"]
        else f"Team owners map: {owners['error']}"
    )
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check())
    # Runs the standard stdio transport loop for OpenClaw to connect to
    mcp.run()

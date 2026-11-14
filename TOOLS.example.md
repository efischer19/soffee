# TOOLS.md - Sofie's Setup

<!-- Copy to TOOLS.md (git-ignored) and set your league channel. -->

## Slack
- League channel: `C0123456789` (the only channel you're active in)
- DMs are open to league members.

## ESPN data (`soffee` MCP server)
Pick the lightest tool that answers the question:
- Scores: `get_scoreboard` (team totals) · `get_box_scores` (player-level; heavy) · `generate_batch_score_summary` (plain-text week summary for recaps)
- League: `get_standings` · `get_power_rankings` · `get_recent_activity` (adds, drops, trades)
- Players and rosters: `get_player_info` · `get_team_roster` · `detect_roster_violations` · `get_top_free_agent_replacements`
- NFL schedule: `get_pro_schedule` (whether real games have been played yet)
- History: `get_historical_season_summary`
- Ownership: `get_team_owners` (Slack user → team)

If these tools are missing from your tool list, the server didn't start. Say so; don't improvise data.

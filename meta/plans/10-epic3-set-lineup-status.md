# feat: Build Python function for starting/benching players

## What do you want to build?

Write a Python function wrapping the `espn-api` write endpoints to move a
player from the bench to the starting lineup, or vice versa.

## Acceptance Criteria

- [ ] Create `set_lineup_status(team_id, player_name, target_slot)` function.
- [ ] Function calls the appropriate `espn-api` endpoint.
- [ ] Function catches ESPN errors (e.g., "player locked") and returns a descriptive error string.

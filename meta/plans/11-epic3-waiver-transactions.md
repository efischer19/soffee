# feat: Build Python function for adding/dropping players

## What do you want to build?

Write a Python function wrapping the `espn-api` write endpoints to execute
free agent additions or waiver wire claims.

## Acceptance Criteria

- [ ] Create `process_waiver_transaction(team_id, player_to_add, player_to_drop, bid_amount)` function.
- [ ] Function executes the add/drop via the API.
- [ ] Function safely handles edge cases (e.g., invalid FAAB bid, player already rostered) and returns clear errors.

# feat: Implement Slack User ID to ESPN Team ID authorization mapping

## What do you want to build?

Create a lightweight authorization mechanism to ensure that when a Slack user
requests a roster move, they actually own the corresponding fantasy team in ESPN.

## Acceptance Criteria

- [ ] Create a static mapping configuration (e.g., a JSON file or dictionary) linking Slack User IDs to ESPN Team IDs.
- [ ] Write a helper function `verify_team_ownership(slack_user_id, target_team_id)` that returns a boolean.

## Implementation Notes (Optional)

A simple hardcoded dictionary is sufficient for Phase v0.

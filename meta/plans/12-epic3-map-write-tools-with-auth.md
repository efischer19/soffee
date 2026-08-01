# feat: Map roster management functions as tools with auth validation

## What do you want to build?

Expose the write actions as tools in `SKILL.md`, ensuring the agent passes the
requesting user's Slack ID so the authorization helper can validate the request.

## Acceptance Criteria

- [ ] Add tool definitions for lineup setting and waiver transactions in `SKILL.md`.
- [ ] Update the system prompt to explicitly require the agent to pass the `slack_user_id` context to these tools.
- [ ] Verify the agent correctly blocks a simulated request from an unauthorized user.

# feat: Verify agent Slack connectivity and mention-handling

## What do you want to build?

Test and ensure the OpenClaw agent can successfully read messages in a channel
and respond appropriately when `@mentioned`.

## Acceptance Criteria

- [ ] Start the local OpenClaw agent.
- [ ] Agent successfully connects to the Slack workspace without authentication errors.
- [ ] Agent reads a test prompt when `@mentioned` in a test channel and successfully replies with a generic response.

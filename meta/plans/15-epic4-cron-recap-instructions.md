# feat: Define system instructions for cron-triggered recaps

## What do you want to build?

Provide specific instructions in the manifest for how the agent should behave
when awakened by a cron job, specifically instructing it to use the summary
data to write a trash-talking recap.

## Acceptance Criteria

- [ ] Add a prompt handler specifically for the cron trigger events.
- [ ] Instruct the agent to execute `generate_batch_score_summary()` upon waking.
- [ ] Instruct the agent to format the resulting data into an engaging, witty channel broadcast and post it.

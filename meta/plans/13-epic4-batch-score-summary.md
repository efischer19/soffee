# feat: Build Python function for matchup summary generation

## What do you want to build?

Write a dedicated Python function designed to pull the current scores and
format them specifically for an automated, bulk Slack update.

## Acceptance Criteria

- [ ] Create `generate_batch_score_summary()` function.
- [ ] Function retrieves all current matchups for the week.
- [ ] Function returns a highly structured, plain-text or Markdown summary of the entire league's scoreboard.

## Implementation Notes (Optional)

This function should not attempt to be conversational itself; it just provides
the raw, clean data block that the LLM will use to generate the conversational
update.

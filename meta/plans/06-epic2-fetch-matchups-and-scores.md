# feat: Build Python function to fetch current week matchups and scores

## What do you want to build?

Write a Python function using the initialized ESPN `League` object to retrieve
the current week's matchups, live box scores, and projected points.

## Acceptance Criteria

- [ ] Create `get_current_matchups()` function.
- [ ] Function queries the ESPN API for current week box scores.
- [ ] Function formats the raw API response into a clean, LLM-readable JSON or string format containing team names, current points, and projected points.
- [ ] Gracefully handle API timeouts or errors.

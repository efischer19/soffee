# feat: Add espn-api dependency and environment configuration

## What do you want to build?

Install the `espn-api` Python library and configure the secure environment
variables required to access a private ESPN fantasy football league.

## Acceptance Criteria

- [ ] Add `espn-api` to `requirements.txt` or `pyproject.toml`.
- [ ] Add `ESPN_SWID`, `ESPN_S2`, `ESPN_LEAGUE_ID`, and `ESPN_YEAR` to `.env.example`.
- [ ] Create a base initialization function in `main.py` that instantiates the `espn_api.football.League` object using these credentials.

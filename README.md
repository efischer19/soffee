# soffee

> **E**ric's **E**SPN **F**antasy **F**ootball **O**penclaw **S**kill, acronymed
> backwards for a better name.

## What Is This?

**Project SOFFEE** is an open-source initiative to build a native,
conversational AI assistant for fantasy football leagues. Deployed as an
[OpenClaw](https://openclaw.dev) skill, the agent assumes the persona of
**"Sofie"** — an autonomous, Slack-native commissioner's assistant.

Sofie bridges the gap between disparate fantasy sports platforms and the modern
chat environments where leagues actually communicate, serving as a data
retrieval engine, roster manager, and automated content generator.

For the full executive summary and phased roadmap, see
[`meta/SOFFEE.md`](./meta/SOFFEE.md).

## Core Philosophy

At its heart, fantasy football serves as a vital social engine for maintaining
lifelong friendships. SOFFEE is engineered to **augment human interaction rather
than automate it away.** Sofie's automated briefings, performance recaps, and
persona are specifically tuned to ignite league banter, cultivate competitive
rivalries, and prompt frequent manager engagement.

## 🔐 Authentication Architecture (Important!)

Sofie does not use a standard OAuth flow for individual league managers. Instead, **she operates entirely using the Commissioner's ESPN credentials.**

Because there is no official, public ESPN Fantasy API, Sofie authenticates by piggybacking on the Commissioner's browser session cookies (`SWID` and `espn_s2`). This gives the bot "Commissioner Access" to execute roster moves for *any* team in the league.

### How this impacts you (The Host)

1. **You must provide your cookies:** To run Sofie, the Commissioner must extract their `SWID` and `espn_s2` cookies from their browser and place them in the `.env` file.
2. **Never share your `.env`:** These cookies provide access to your *entire* ESPN account. **DO NOT commit them to GitHub.** If you are not the one hosting the OpenClaw server, you must implicitly trust the person who is.
3. **The Slack ID mapping says who owns which team.** Today Sofie is read-only (see Status below): `SOFFEE_SLACK_USER_TO_TEAM_MAP` is how she answers "who owns what" without guessing. If roster actions come back, this mapping becomes the firewall again: commissioner cookies can change *any* team, so every move must be checked against the real Slack user who asked.

### Finding your ESPN Cookies

1. Log into your ESPN Fantasy account on a desktop browser.
2. Right-click anywhere and select **Inspect** to open Developer Tools.
3. Go to the **Application** (Chrome/Edge) or **Storage** (Firefox) tab.
4. Under the **Cookies** section, select `http://fantasy.espn.com`.
5. Find the `SWID` value (looks like `{UUID}`) and the `espn_s2` value (a very long string).
6. Paste these into your `.env` file.

## Phased Roadmap

| Phase | Focus | Architecture |
| :--- | :--- | :--- |
| **v0** | Slack MVP | Monolithic OpenClaw skill (ESPN hardcoded) |
| **v1** | Architecture Refactor | `soffee-core` (PyPI) + `soffee-skill` (ClawHub) |
| **v2+** | Multi-Platform | Universal Interface + provider adapters |

### Status (November 2026)

**v0 runs as an MCP server, read-only.** `main.py` is a [Model Context Protocol](https://modelcontextprotocol.io) server (FastMCP, stdio) with 13 read-only tools: scoreboard, box scores, NFL schedule, standings, power rankings, recent activity, player info, rosters, roster violations, free-agent replacements, a recap summary, season history and team owners. OpenClaw starts it as an MCP server, and Sofie's persona and rules live alongside it (below).

What changed from the original v0 plan, and why:
- **MCP instead of a ClawHub skill.** Any MCP client can use the tools (OpenClaw, Claude, other agent harnesses), which is most of what v1's "thin wrapper" was for.
- **No roster actions yet** (start/sit, add/drop, the Sunday roster sweep). They need the Slack-actor authorization above done properly; they'll return as separate tools.
- **Scheduled recaps are OpenClaw cron jobs** that wake Sofie with the instructions in `AGENTS.md`, not code here.

v1 (the `soffee-core` split and the provider interface) still applies: the ESPN logic moves out of `main.py` into a library, and the MCP server becomes the thin layer that depends on it.

## Repository Structure

The repo root doubles as Sofie's OpenClaw workspace.

| Path | Purpose |
| :--- | :--- |
| `main.py` | The MCP server (`uv run main.py`; `uv run main.py --check` tests the ESPN connection) |
| `tests/` | pytest suite (ESPN is mocked) |
| `SOUL.md`, `IDENTITY.md`, `AGENTS.md`, `HEARTBEAT.md` | Sofie's persona, identity, rules and heartbeat, loaded by OpenClaw |
| `USER.example.md`, `TOOLS.example.md` | Templates for your league's specifics. Copy to `USER.md` / `TOOLS.md` (git-ignored) |
| `.env.example` | ESPN credentials and the Slack-to-team map. Copy to `.env` (git-ignored) |
| `meta/` | The executive summary (`SOFFEE.md`), ADRs and plans |
| `issues/` | A plain-markdown to-do list (GitHub issues hold the v1 roadmap) |
| `scripts/` | Local CI and docs helpers |

## Key Tooling Decisions (ADRs)

| ADR | Decision |
| :--- | :--- |
| [ADR-002](meta/adr/ADR-002-use_python312.md) | Python 3.12+ as minimum version |
| [ADR-015](meta/adr/ADR-015-use_uv.md) | uv for dependency management |
| [ADR-004](meta/adr/ADR-004-use_pytest.md) | pytest for testing |
| [ADR-005](meta/adr/ADR-005-use_ruff.md) | Ruff for linting and formatting |
| [ADR-006](meta/adr/ADR-006-use_docker.md) | Docker for containerization |
| [ADR-007](meta/adr/ADR-007-monorepo_apps_structure.md) | Monorepo /apps structure |

See `meta/adr/` for the full list of Architecture Decision Records.

## Slack Workspace Setup

Sofie connects to your Slack workspace using [Slack Socket Mode](https://slack.dev/python-slack-sdk/socket-mode/), a secure, bidirectional connection managed by the OpenClaw framework.

### Required OAuth Scopes

To deploy Sofie, your Slack App must request the following OAuth scopes:

| Scope | Purpose |
| :--- | :--- |
| `chat:write` | Post messages to channels and direct messages |
| `chat:write.public` | Post to public channels |
| `reactions:read` | Read message reactions |
| `channels:read` | List and view channel information |
| `users:read` | Read user profiles and information |

### Event Subscriptions

Enable Event Subscriptions in your Slack App and subscribe to:

- `app_mention` — Listen for mentions of Sofie
- `message.channels` — Listen to channel messages
- `message.im` — Listen to direct messages

### Running it with OpenClaw

1. Clone this repo where OpenClaw can reach it; that folder is Sofie's workspace.
2. `cp .env.example .env`, `cp USER.example.md USER.md`, `cp TOOLS.example.md TOOLS.md`, and fill them in.
3. `uv run main.py --check` should print your league's name and team count.
4. In `openclaw.json`, point Sofie's agent at the folder and register the server:

```json5
agents: { list: [ { id: "sofie", workspace: "/path/to/soffee", /* ... */ } ] },
mcp: { servers: { soffee: { command: "uv", args: ["run", "main.py"], cwd: "/path/to/soffee" } } },
```

Slack itself (the tokens and Socket Mode above) is configured in OpenClaw's Slack channel, not here.

## Getting Started

```bash
# Python 3.12+ and uv (https://docs.astral.sh/uv/)
uv sync
uv run pytest

# Quality checks (ruff, markdownlint and friends), the same as CI
pre-commit install
pre-commit run --all-files
```

## License

This project is licensed under the [MIT License](./LICENSE.md).

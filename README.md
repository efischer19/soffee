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

## Phased Roadmap

| Phase | Focus | Architecture |
| :--- | :--- | :--- |
| **v0** | Slack MVP | Monolithic OpenClaw skill (ESPN hardcoded) |
| **v1** | Architecture Refactor | `soffee-core` (PyPI) + `soffee-skill` (ClawHub) |
| **v2+** | Multi-Platform | Universal Interface + provider adapters |

## Repository Structure

| Path | Purpose |
| :--- | :--- |
| `apps/` | Standalone Python applications, each with its own `pyproject.toml` |
| `libs/` | Shared Python libraries used across applications |
| `testing/` | Shared test utilities, fixtures, and helpers |
| `scripts/` | Utility and automation scripts |
| `templates/` | Template files for scaffolding new apps and libs |
| `meta/adr/` | Architecture Decision Records — the logbook of *why* decisions were made |
| `meta/plans/` | Project plans and roadmaps |
| `docs-src/` | Source files for generated documentation (MkDocs) |
| `.github/` | GitHub-specific configuration (issue templates, PR templates, CI workflows) |

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

### Environment Configuration

Once your Slack App is configured, set the following environment variables:

```bash
SLACK_APP_TOKEN=xapp-1-XXXXXXXXXXXXXXX    # Socket Mode App Token
SLACK_BOT_TOKEN=xoxb-XXXXXXXXXXXXXXX      # Bot User OAuth Token
```

See `.env.example` for a template. For detailed setup instructions, refer to the [Configuration section in SKILL.md](./SKILL.md#configuration).

## Getting Started

```bash
# Install Python 3.12+
pyenv install 3.12
pyenv local 3.12

# Install uv
pip install uv

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run local quality checks
./scripts/local-ci-check.sh
```

## License

This project is licensed under the [MIT License](./LICENSE.md).

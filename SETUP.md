# SOFFEE Setup & Deployment Guide

## Configuration

### Slack Socket Mode Authentication

Sofie connects to your Slack workspace using native [Slack Socket Mode](https://slack.dev/python-slack-sdk/socket-mode/), which provides a secure, bidirectional WebSocket connection managed by the OpenClaw framework.

To enable Slack integration, configure the following environment variables:

#### Required Environment Variables

- **`SLACK_APP_TOKEN`**: Socket Mode App Token (format: `xapp-1-XXXXXXXXXXXXXXX`)
  - Enables Socket Mode WebSocket connection
  - Generated in Slack App settings under "Socket Mode"

- **`SLACK_BOT_TOKEN`**: Bot User OAuth Token (format: `xoxb-XXXXXXXXXXXXXXX`)
  - Authenticates API calls and message posting
  - Generated in Slack App settings under "OAuth & Permissions"

- **`ESPN_SWID`**: ESPN SWID cookie value (format: `{UUID}`)
  - Authenticates Sofie to ESPN as the league commissioner

- **`ESPN_S2`**: ESPN `espn_s2` cookie value
  - Required to access private league data and roster actions

- **`ESPN_LEAGUE_ID`**: ESPN fantasy football league ID
  - Found in the ESPN league URL

- **`ESPN_YEAR`**: Active ESPN season year (for example `2025`)
  - Update this every season so Sofie reads and writes against the correct league year

- **`SOFFEE_SLACK_USER_TO_TEAM_MAP`**: JSON object mapping Slack user IDs to ESPN team IDs
  - Example: `{"U1234567890": 1, "U0987654321": 2}`
  - This mapping is the authorization boundary for roster actions

#### Setup Instructions

1. **Create or open a Slack App**
   - Visit [Slack API dashboard](https://api.slack.com/apps)
   - Create a new app or select an existing one

2. **Enable Socket Mode**
   - Navigate to "Socket Mode" in the left menu
   - Toggle "Enable Socket Mode" on
   - Copy the generated **App Token** (starts with `xapp-1-`)

3. **Configure OAuth Scopes**
   - Navigate to "OAuth & Permissions"
   - See [Required OAuth Scopes](#required-oauth-scopes) section below
   - Copy the **Bot Token** (starts with `xoxb-`)

4. **Set Environment Variables**
   - Add `SLACK_APP_TOKEN` and `SLACK_BOT_TOKEN` to your environment
   - Example `.env` file:

   ```bash
   SLACK_APP_TOKEN=xapp-1-XXXXXXXXXXXXXXX
   SLACK_BOT_TOKEN=xoxb-XXXXXXXXXXXXXXX
   ESPN_SWID={YOUR-ESPN-SWID}
   ESPN_S2=YOUR_ESPN_S2_COOKIE
   ESPN_LEAGUE_ID=123456
   ESPN_YEAR=2025
   SOFFEE_SLACK_USER_TO_TEAM_MAP='{"U1234567890": 1, "U0987654321": 2}'
   ```

### Required OAuth Scopes

The following OAuth scopes must be granted to the Slack App for Sofie to function:

#### Message & Conversation Scopes

- `chat:write` — Post messages to channels and direct messages
- `chat:write.public` — Post in public channels
- `reactions:read` — Read message reactions
- `channels:read` — List channels

#### User & Profile Scopes

- `users:read` — Read user profiles and information

#### Event Subscriptions

- Enable "Event Subscriptions" and subscribe to:
  - `app_mention` — Respond when mentioned
  - `message.channels` — Receive channel messages
  - `message.im` — Receive direct messages

### Automated Broadcast Configuration

Sofie can be configured to automatically broadcast NFL window summaries and post-game briefings at scheduled times. These automated broadcasts help keep your league engaged with timely updates without requiring manual triggers.

#### Broadcast Schedule

Sofie is configured with five default automated schedules aligned with standard NFL windows:

- **Sunday 10 AM EST** — Automated roster violation sweep
- **Sunday 12 PM EST** — Early Sunday games
- **Sunday 4:30 PM EST** — Mid-afternoon slate
- **Sunday 8 PM EST** — Sunday night football
- **Monday/Tuesday 7 AM EST** — Post-game morning briefing

#### Environment Variables

Configure the broadcast channel and cron schedules using these environment variables:

- **`SOFFEE_BROADCAST_CHANNEL`** — Slack channel for automated broadcasts
  - Format: Channel name (e.g., `#nfl-updates`) or channel ID (e.g., `C1234567890`)
  - Default: `#nfl-updates`

- **`SOFFEE_CRON_SUNDAY_10AM`** — Cron pattern for Sunday 10 AM EST roster sweep
  - Default: `0 15 * * 0` (15:00 UTC)
  - Example: `0 10 * * 0` for 10:00 UTC

- **`SOFFEE_CRON_SUNDAY_12PM`** — Cron pattern for Sunday 12 PM EST
  - Default: `0 17 * * 0` (17:00 UTC)
  - Example: `0 12 * * 0` for 12:00 UTC

- **`SOFFEE_CRON_SUNDAY_430PM`** — Cron pattern for Sunday 4:30 PM EST
  - Default: `30 21 * * 0` (21:30 UTC)
  - Example: `30 16 * * 0` for 16:30 UTC

- **`SOFFEE_CRON_SUNDAY_8PM`** — Cron pattern for Sunday 8 PM EST
  - Default: `0 1 * * 1` (01:00 UTC Monday)
  - Example: `0 20 * * 0` for 20:00 UTC Sunday

- **`SOFFEE_CRON_MONDAY_TUESDAY_7AM`** — Cron pattern for Monday/Tuesday 7 AM EST
  - Default: `0 12 * * 1,2` (12:00 UTC Mon/Tue)
  - Example: `0 7 * * 1,2` for 07:00 UTC Mon/Tue

#### Cron Syntax

Cron patterns use standard Unix cron format with five space-separated fields:

```bash
minute hour day-of-month month day-of-week
```

- **minute**: 0-59
- **hour**: 0-23 (UTC)
- **day-of-month**: 1-31
- **month**: 1-12
- **day-of-week**: 0-6 (0 = Sunday)

Special characters:

- `*` — Match any value
- `,` — Match multiple values (e.g., `1,2,3`)
- `-` — Match a range (e.g., `1-5`)
- `/` — Step values (e.g., `*/15` for every 15 minutes)

## Usage

Invoke Sofie in your Slack channel with natural language queries:

```text
@Sofie What's my score this week?
@Sofie Show me the waiver wire
@Sofie Start Cooper Kupp on my team
```

For more information, visit the [SOFFEE GitHub repository](https://github.com/efischer19/soffee).


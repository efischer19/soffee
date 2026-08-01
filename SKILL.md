---
name: soffee
description: An autonomous, Slack-native commissioner's assistant for fantasy football leagues. Handles league queries, roster management, and automated content generation via conversational AI.
homepage: https://github.com/efischer19/soffee
user-invocable: true
disable-model-invocation: false
license: MIT
compatibility: Requires OpenClaw framework and Slack Socket Mode integration
metadata:
  openclaw:
    emoji: "🏈"
---

# SOFFEE - OpenClaw Fantasy Football Skill

**Sofie** is an autonomous, Slack-native commissioner's assistant for fantasy football leagues. This OpenClaw skill brings fantasy football data directly to league members via conversational AI, enabling queries, roster management, and automated content generation without leaving Slack.

## Core Capabilities

- **League Queries**: Answer fantasy football questions in natural language (e.g., "What's the score of my matchup?", "Who's on the waiver wire?")
- **Roster Management**: Execute public channel roster actions (Start, Sit, Add, Drop)
- **Automated Briefings**: Generate and broadcast NFL window summaries and performance recaps
- **Engagement-Focused**: Craft responses designed to ignite league banter and competitive rivalry

## Philosophy

Fantasy football is fundamentally a social experience. SOFFEE augments human interaction rather than automates it away. Every automated briefing, roster update, and response is designed to invite human dialogue and keep league members engaged.

## Technical Details

- **Data Source**: ESPN Fantasy Football API (via espn-api)
- **Environment**: OpenClaw execution with Slack Socket Mode integration
- **Architecture**: Phase v0 monolithic deployment
- **Output**: Slack channel messages and direct member interactions

## Usage

Invoke Sofie in your Slack channel with natural language queries:

```
@Sofie What's my score this week?
@Sofie Show me the waiver wire
@Sofie Start Cooper Kupp on my team
```

For more information, visit the [SOFFEE GitHub repository](https://github.com/efischer19/soffee).

# **Executive Summary: Project SOFFEE**

Eric's ESPN Fantasy Football Openclaw Skill, acronymed backwards for a better name

## **1\. Project Overview & Persona**

*Project SOFFEE is an open-source initiative to build a native, conversational AI assistant for fantasy football leagues.*
Deployed as an OpenClaw skill, the agent assumes the persona of **"Sofie"** — an autonomous, Slack-native commissioner’s assistant. Sofie bridges the gap between disparate fantasy sports platforms and the modern chat environments where leagues actually communicate, serving as a data retrieval engine, roster manager, and automated content generator.

## **2\. Core Philosophy: Amplifying Human Connection**

At its heart, fantasy football serves as a vital social engine for maintaining lifelong friendships. Project SOFFEE is engineered to **augment human interaction rather than automate it away.**
Sofie functions as a conversational bridge within the league ecosystem. Her automated briefings, performance recaps, and persona are specifically tuned to ignite league banter, cultivate competitive rivalries, and prompt frequent manager engagement. She is designed to provide members with more opportunities for discourse, avoiding the role of a sterile, transactional interface that might otherwise erode the social foundation of the sport.

## **3\. The Problem**

Fantasy football commissioners and league members face several persistent friction points:

* **Siloed Data:** Checking scores, player statuses, or waiver wire availability requires leaving the league chat and navigating a separate fantasy app.
* **Repetitive Commish Duties:** Commissioners manually track and announce weekly summaries, injury alerts, and transaction notifications.
* **Fragmented Ecosystems:** There is no universal API for fantasy football. Platforms like ESPN, Sleeper, and Yahoo have distinct, often undocumented APIs with completely different authentication flows, making multi-platform tool development prohibitively difficult for independent developers.

## **4\. The Solution**

Sofie solves this by bringing the fantasy platform directly to the users via a conversational interface.
Leveraging the OpenClaw framework, Sofie connects to the league's Slack workspace (via Socket Mode) to listen, respond, and act. Instead of navigating an app, managers simply ask Sofie questions or issue commands in natural language. Under the hood, Sofie translates these intents into programmatic actions against the fantasy provider's API.

## **5\. Technical Strategy & Phased Roadmap**

To balance the immediate need for a functional MVP with the long-term goal of building a multi-platform standard, development is strictly phased.

### **Phase v0: The Slack MVP (Monolith)**

* **Focus:** Speed to deployment for the immediate season.
* **Architecture:** A monolithic OpenClaw skill (published exclusively to ClawHub).
* **Data Source:** Hardcoded to use the espn-api Python library.
* **Features:**
  * Read-only Slack queries (e.g., "What's the score of my matchup?").
  * Public channel roster actions (Start, Sit, Add, Drop).
  * Automated cron job broadcasts (NFL window summaries).

### **Phase v1: The Architecture Refactor (Split Distribution)**

* **Focus:** Decoupling logic for broader open-source adoption.
* **Architecture:** Split the monolith into two distinct packages.
  1. **soffee-core (PyPI):** A pure Python package containing all API fetching, data modeling, and business logic.
  2. **soffee-skill (ClawHub):** A lightweight OpenClaw wrapper that imports soffee-core to handle LLM routing and Slack I/O.
* **Engineering Pattern:** Implement the **Adapter Design Pattern**. Establish a "Universal Interface" (UniversalTeam, UniversalMatchup) so the agent logic remains isolated from the specific fantasy platform's data shape. Create the ESPNProvider to map espn-api data to this universal format.

### **Phase v2+: Multi-Platform Generalization ("The One Ring")**

* **Focus:** Becoming the definitive OpenClaw fantasy sports skill.
* **Features:** Utilizing the Universal Interface established in v1, introduce new data providers (e.g., SleeperProvider, YahooProvider). This allows any league to use Sofie simply by updating a config flag, without requiring changes to the core AI prompts or routing logic.

## **6\. Note for LLM Assistants (Copilot Context)**

When generating code, scaffolding, or writing tests for this repository:

> 1. **Adhere to the Phased Roadmap:** Do not attempt to build Universal Interfaces or Split Architecture components if working on v0 tickets. v0 is intentionally monolithic and hardcoded for ESPN.
> 2. **Prioritize espn-api:** All initial data fetching must leverage the community espn-api library. Do not attempt to write raw HTTP requests to ESPN's undocumented endpoints unless the library lacks the required functionality.
> 3. **Environment:** Assume an OpenClaw execution environment where standard output and standard error are captured by the agent framework, and Slack messaging is handled natively by the OpenClaw gateway.
> 4. **Design for Engagement, Not Automation:** When generating persona prompts, automated recaps, or Slack messages, always craft them to invite human response. Prioritize banter, matchup highlights, close finishes, and lighthearted callouts over plain data dumps. The goal of every agent output is to get human league members talking in the channel.

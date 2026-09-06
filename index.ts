import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import { Type } from "@sinclair/typebox";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

export default function register(api: OpenClawPluginApi) {
  
  // 1. Get Current Matchups
  api.registerTool({
    name: "get_current_matchups",
    description: "Retrieve current week's matchups with live scores and projected final points",
    parameters: Type.Object({}),
    async execute(_id, params) {
      const { stdout, stderr } = await execAsync("uv run python main.py get-current-matchups");
      if (stderr) console.error(stderr);
      return { content: [{ type: "text", text: stdout }] };
    },
  });

  // 2. Get Team Roster
  api.registerTool({
    name: "get_team_roster",
    description: "Get a team's active roster with player positions and injury statuses",
    parameters: Type.Object({
      team_name: Type.String({ 
        description: "The name of the team to retrieve the roster for. Supports partial name matching and case-insensitive search." 
      })
    }),
    async execute(_id, params) {
      // Escaping quotes for shell execution
      const { stdout, stderr } = await execAsync(`uv run python main.py get-team-roster "${params.team_name}"`);
      if (stderr) console.error(stderr);
      return { content: [{ type: "text", text: stdout }] };
    },
  });

  // 3. Set Lineup Status
  api.registerTool({
    name: "set_lineup_status",
    description: "Move a player to a specific lineup slot (start, bench, or IR) for the user's own team after sourcing slack_user_id from Slack context and verifying ownership",
    parameters: Type.Object({
      slack_user_id: Type.String({ description: "The Slack User ID of the requesting user (format: UXXXXXXXX)." }),
      team_id: Type.Number({ description: "The ESPN Team ID for the team to update." }),
      player_name: Type.String({ description: "The full name of the player to move." }),
      target_slot: Type.String({ description: "The target lineup slot position. Valid values: 'QB', 'RB', 'WR', 'TE', 'K', 'DEF', 'BENCH', 'IR'." })
    }),
    async execute(_id, params) {
      const command = `uv run python main.py set-lineup-status "${params.slack_user_id}" ${params.team_id} "${params.player_name}" "${params.target_slot}"`;
      const { stdout, stderr } = await execAsync(command);
      if (stderr) console.error(stderr);
      return { content: [{ type: "text", text: stdout }] };
    },
  });

  // 4. Process Waiver Transaction
  api.registerTool({
    name: "process_waiver_transaction",
    description: "Process a waiver wire claim or free agent pickup for the user's own team after sourcing slack_user_id from Slack context and verifying ownership",
    parameters: Type.Object({
      slack_user_id: Type.String({ description: "The Slack User ID of the requesting user." }),
      team_id: Type.Number({ description: "The ESPN Team ID for the team processing the transaction." }),
      player_to_add: Type.String({ description: "The full name of the player to add." }),
      player_to_drop: Type.Optional(Type.String({ description: "The full name of the player to drop. Leave undefined for free agent pickups without dropping." })),
      bid_amount: Type.Number({ description: "The FAAB bid amount in currency units (e.g., 1-999). Use 0 for free agent pickups." })
    }),
    async execute(_id, params) {
      const dropArg = params.player_to_drop ? `"${params.player_to_drop}"` : "null";
      const command = `uv run python main.py process-waiver-transaction "${params.slack_user_id}" ${params.team_id} "${params.player_to_add}" ${dropArg} ${params.bid_amount}`;
      const { stdout, stderr } = await execAsync(command);
      if (stderr) console.error(stderr);
      return { content: [{ type: "text", text: stdout }] };
    },
  });

  // 5. Generate Batch Score Summary
  api.registerTool({
    name: "generate_batch_score_summary",
    description: "Generate a structured, plain-text summary of the entire league's scoreboard for the current week",
    parameters: Type.Object({}),
    async execute(_id, params) {
      const { stdout, stderr } = await execAsync("uv run python main.py generate-batch-score-summary");
      if (stderr) console.error(stderr);
      return { content: [{ type: "text", text: stdout }] };
    },
  });

  // 6. Get Historical Season Summary
  api.registerTool({
    name: "get_historical_season_summary",
    description: "Retrieve historical season data including standings and final statistics for a given year",
    parameters: Type.Object({
      year: Type.Number({ description: "The season year to retrieve historical data for (e.g., 2024, 2025)." })
    }),
    async execute(_id, params) {
      const { stdout, stderr } = await execAsync(`uv run python main.py get-historical-season-summary ${params.year}`);
      if (stderr) console.error(stderr);
      return { content: [{ type: "text", text: stdout }] };
    },
  });
}

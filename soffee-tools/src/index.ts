import { Type } from "@sinclair/typebox";
import { defineToolPlugin } from "openclaw/plugin-sdk/tool-plugin";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

export default defineToolPlugin({
  id: "soffee",
  name: "SOFFEE",
  description: "An autonomous, Slack-native commissioner's assistant for fantasy football leagues.",
  tools: (tool) => [
    tool({
      name: "get_current_matchups",
      description: "Retrieve current week's matchups with live scores and projected final points",
      parameters: Type.Object({}),
      async execute() {
        const { stdout, stderr } = await execAsync("uv run python main.py get-current-matchups");
        if (stderr) console.error(stderr);
        return stdout.trim();
      },
    }),

    tool({
      name: "get_team_roster",
      description: "Get a team's active roster with player positions and injury statuses",
      parameters: Type.Object({
        team_name: Type.String({
          description: "The name of the team to retrieve the roster for. Supports partial name matching and case-insensitive search."
        })
      }),
      async execute({ team_name }) {
        const { stdout, stderr } = await execAsync(`uv run python main.py get-team-roster "${team_name}"`);
        if (stderr) console.error(stderr);
        return stdout.trim();
      },
    }),

    tool({
      name: "set_lineup_status",
      description: "Move a player to a specific lineup slot (start, bench, or IR) for the user's own team after sourcing slack_user_id from Slack context and verifying ownership",
      parameters: Type.Object({
        slack_user_id: Type.String({ description: "The Slack User ID of the requesting user (format: UXXXXXXXX)." }),
        team_id: Type.Number({ description: "The ESPN Team ID for the team to update." }),
        player_name: Type.String({ description: "The full name of the player to move." }),
        target_slot: Type.String({ description: "The target lineup slot position. Valid values: 'QB', 'RB', 'WR', 'TE', 'K', 'DEF', 'BENCH', 'IR'." })
      }),
      async execute({ slack_user_id, team_id, player_name, target_slot }) {
        const command = `uv run python main.py set-lineup-status "${slack_user_id}" ${team_id} "${player_name}" "${target_slot}"`;
        const { stdout, stderr } = await execAsync(command);
        if (stderr) console.error(stderr);
        return stdout.trim();
      },
    }),

    tool({
      name: "process_waiver_transaction",
      description: "Process a waiver wire claim or free agent pickup for the user's own team after sourcing slack_user_id from Slack context and verifying ownership",
      parameters: Type.Object({
        slack_user_id: Type.String({ description: "The Slack User ID of the requesting user." }),
        team_id: Type.Number({ description: "The ESPN Team ID for the team processing the transaction." }),
        player_to_add: Type.String({ description: "The full name of the player to add." }),
        player_to_drop: Type.Optional(Type.String({ description: "The full name of the player to drop. Leave undefined for free agent pickups without dropping." })),
        bid_amount: Type.Number({ description: "The FAAB bid amount in currency units (e.g., 1-999). Use 0 for free agent pickups." })
      }),
      async execute({ slack_user_id, team_id, player_to_add, player_to_drop, bid_amount }) {
        const dropArg = player_to_drop ? `"${player_to_drop}"` : "null";
        const command = `uv run python main.py process-waiver-transaction "${slack_user_id}" ${team_id} "${player_to_add}" ${dropArg} ${bid_amount}`;
        const { stdout, stderr } = await execAsync(command);
        if (stderr) console.error(stderr);
        return stdout.trim();
      },
    }),

    tool({
      name: "generate_batch_score_summary",
      description: "Generate a structured, plain-text summary of the entire league's scoreboard for the current week",
      parameters: Type.Object({}),
      async execute() {
        const { stdout, stderr } = await execAsync("uv run python main.py generate-batch-score-summary");
        if (stderr) console.error(stderr);
        return stdout.trim();
      },
    }),

    tool({
      name: "get_historical_season_summary",
      description: "Retrieve historical season data including standings and final statistics for a given year",
      parameters: Type.Object({
        year: Type.Number({ description: "The season year to retrieve historical data for (e.g., 2024, 2025)." })
      }),
      async execute({ year }) {
        const { stdout, stderr } = await execAsync(`uv run python main.py get-historical-season-summary ${year}`);
        if (stderr) console.error(stderr);
        return stdout.trim();
      },
    }),
  ],
});

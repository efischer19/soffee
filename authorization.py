"""Authorization module for Slack User ID to ESPN Team ID mapping.

This module provides utilities to verify that a Slack user owns a specific
ESPN fantasy football team. Phase v0 supports either a hardcoded fallback
dictionary or an environment-provided JSON mapping.
"""

import json
import os

# Mapping of Slack User IDs to ESPN Team IDs
# Phase v0: Simple hardcoded dictionary
# Format: {"slack_user_id": espn_team_id, ...}
SLACK_USER_TO_TEAM_MAPPING = {
    # Example entries - replace with actual Slack User IDs and ESPN Team IDs
    # "U1234567890": 1,  # Slack user U1234567890 owns ESPN team with ID 1
    # "U0987654321": 2,  # Slack user U0987654321 owns ESPN team with ID 2
}


def _load_slack_user_to_team_mapping() -> dict[str, int]:
    """Load and validate the Slack-to-ESPN team mapping.

    The preferred configuration source is the ``SOFFEE_SLACK_USER_TO_TEAM_MAP``
    environment variable, which should contain a JSON object like
    ``{"U1234567890": 1, "U0987654321": 2}``.

    Returns:
        A normalized mapping of Slack user IDs to positive ESPN team IDs.
        Invalid or ambiguous mappings fail closed and return an empty mapping.
    """
    raw_mapping: object = SLACK_USER_TO_TEAM_MAPPING
    env_mapping = os.environ.get("SOFFEE_SLACK_USER_TO_TEAM_MAP", "").strip()

    if env_mapping:
        try:
            raw_mapping = json.loads(env_mapping)
        except json.JSONDecodeError:
            return {}

    if not isinstance(raw_mapping, dict):
        return {}

    normalized_mapping: dict[str, int] = {}
    seen_team_ids: set[int] = set()

    for raw_slack_user_id, raw_team_id in raw_mapping.items():
        if not isinstance(raw_slack_user_id, str):
            return {}

        slack_user_id = raw_slack_user_id.strip()
        if not slack_user_id:
            return {}

        if isinstance(raw_team_id, bool):
            return {}

        try:
            team_id = int(raw_team_id)
        except (TypeError, ValueError):
            return {}

        if team_id <= 0 or team_id in seen_team_ids:
            return {}

        normalized_mapping[slack_user_id] = team_id
        seen_team_ids.add(team_id)

    return normalized_mapping


def verify_team_ownership(slack_user_id: str, target_team_id: int) -> bool:
    """Verify that a Slack user owns a specific ESPN team.

    Args:
        slack_user_id: The Slack User ID (format: UXXXXXXXX or similar).
        target_team_id: The ESPN Team ID to verify ownership of.

    Returns:
        True if the Slack user owns the target ESPN team, False otherwise.

    Example:
        >>> verify_team_ownership("U1234567890", 1)
        True
        >>> verify_team_ownership("U1234567890", 999)
        False
    """
    if not isinstance(slack_user_id, str) or not slack_user_id:
        return False

    if not isinstance(target_team_id, int) or target_team_id <= 0:
        return False

    user_team_id = _load_slack_user_to_team_mapping().get(slack_user_id.strip())
    return user_team_id == target_team_id


def get_slack_user_for_team(team_id: int) -> str | None:
    """Get the Slack User ID for an ESPN team.

    Performs a reverse lookup to find which Slack user owns a specific ESPN team.
    This is useful for automatically tagging the correct manager in messages.

    Args:
        team_id: The ESPN Team ID to look up.

    Returns:
        str: The Slack User ID if found, None otherwise.

    Example:
        >>> get_slack_user_for_team(1)
        "U1234567890"
        >>> get_slack_user_for_team(999)
        None
    """
    if not isinstance(team_id, int) or team_id <= 0:
        return None

    for slack_user_id, mapped_team_id in _load_slack_user_to_team_mapping().items():
        if mapped_team_id == team_id:
            return slack_user_id

    return None

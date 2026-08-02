"""Authorization module for Slack User ID to ESPN Team ID mapping.

This module provides utilities to verify that a Slack user owns a specific
ESPN fantasy football team. Phase v0 uses a simple hardcoded dictionary
for the mapping.

For production use, this would be replaced with a database lookup or
environment-based configuration.
"""

# Mapping of Slack User IDs to ESPN Team IDs
# Phase v0: Simple hardcoded dictionary
# Format: {"slack_user_id": espn_team_id, ...}
SLACK_USER_TO_TEAM_MAPPING = {
    # Example entries - replace with actual Slack User IDs and ESPN Team IDs
    # "U1234567890": 1,  # Slack user U1234567890 owns ESPN team with ID 1
    # "U0987654321": 2,  # Slack user U0987654321 owns ESPN team with ID 2
}


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

    user_team_id = SLACK_USER_TO_TEAM_MAPPING.get(slack_user_id)
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

    for slack_user_id, mapped_team_id in SLACK_USER_TO_TEAM_MAPPING.items():
        if mapped_team_id == team_id:
            return slack_user_id

    return None

"""Tool for managing resume version history stored locally."""

import json
import os
import uuid
from datetime import datetime, timezone

from strands import tool

VERSIONS_DIR = os.environ.get("VERSIONS_DIR", ".versions")


def _ensure_session_dir(session_id: str) -> str:
    """Create and return the session versions directory."""
    session_dir = os.path.join(VERSIONS_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    return session_dir


def _save_version(
    session_id: str, html_content: str, feedback: str | None = None
) -> dict:
    """Save a new version and return the VersionRecord."""
    session_dir = _ensure_session_dir(session_id)
    version_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    record = {
        "version_id": version_id,
        "session_id": session_id,
        "timestamp": timestamp,
        "html_content": html_content,
        "feedback": feedback,
    }

    version_file = os.path.join(session_dir, f"{version_id}.json")
    with open(version_file, "w") as f:
        json.dump(record, f)

    return record


def _list_versions(session_id: str) -> list[dict]:
    """List all versions for a session, ordered by timestamp desc."""
    session_dir = os.path.join(VERSIONS_DIR, session_id)
    if not os.path.exists(session_dir):
        return []

    versions = []
    for fname in os.listdir(session_dir):
        if fname.endswith(".json"):
            with open(os.path.join(session_dir, fname)) as f:
                versions.append(json.load(f))

    versions.sort(key=lambda v: v["timestamp"], reverse=True)
    return versions


@tool
def manage_versions(
    action: str,
    session_id: str,
    html_content: str = "",
    version_id: str = "",
    feedback: str = "",
) -> dict:
    """Manage resume version history stored locally.

    Actions:
      - "save": Store a new version. Requires html_content.
      - "get_latest": Retrieve the most recent version for a session.
      - "get": Retrieve a specific version by version_id.
      - "list": List all versions for a session.

    Args:
        action: One of "save", "get_latest", "get", "list".
        session_id: UUID string identifying the session.
        html_content: HTML content to save (required for "save").
        version_id: Version ID to retrieve (required for "get").
        feedback: Feedback text that produced this version.

    Returns:
        A dict with the version record(s) or operation result.
    """
    valid_actions = {"save", "get_latest", "get", "list"}
    if action not in valid_actions:
        raise ValueError(f"action must be one of {valid_actions}")
    if not session_id:
        raise ValueError("session_id is required")

    if action == "save":
        if not html_content:
            raise ValueError("html_content is required for save action")
        record = _save_version(session_id, html_content, feedback or None)
        return {"status": "saved", "record": record}

    elif action == "get_latest":
        versions = _list_versions(session_id)
        if not versions:
            return {"status": "empty", "record": {}}
        return {"status": "found", "record": versions[0]}

    elif action == "get":
        if not version_id:
            raise ValueError("version_id is required for get action")
        versions = _list_versions(session_id)
        for v in versions:
            if v["version_id"] == version_id:
                return {"status": "found", "record": v}
        raise ValueError(f"Version {version_id} not found")

    elif action == "list":
        versions = _list_versions(session_id)
        return {"status": "found", "count": len(versions), "versions": versions}

"""
Step 3: Version Management with S3
====================================

The final tool — manage_versions — stores and retrieves resume
versions in S3. This enables:
- Saving each generated resume as a version
- Listing all versions for a session
- Retrieving a specific version
- Iterative refinement (generate → feedback → new version)

Each version is a JSON file in S3 at:
  s3://<bucket>/versions/<session_id>/<version_id>.json

This step demonstrates the tool standalone (without the full agent)
to understand the S3 operations clearly.

Prerequisites:
- S3 bucket from Lab 2 setup
- Set RESUME_S3_BUCKET environment variable

Run: uv run python step3_version_management.py
"""

import json
import os
import uuid
from datetime import datetime, timezone

import boto3

AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
S3_BUCKET = os.environ.get("RESUME_S3_BUCKET")

if not S3_BUCKET:
    print("ERROR: Set RESUME_S3_BUCKET environment variable first.")
    exit(1)

s3 = boto3.client("s3", region_name=AWS_REGION)


def save_version(session_id: str, html_content: str, feedback: str = None) -> dict:
    """Save a new resume version to S3."""
    version_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    record = {
        "version_id": version_id,
        "session_id": session_id,
        "timestamp": timestamp,
        "html_content": html_content,
        "feedback": feedback,
    }

    key = f"versions/{session_id}/{version_id}.json"
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=json.dumps(record))
    print(f"  Saved version {version_id[:8]}... at {timestamp}")
    return record


def list_versions(session_id: str) -> list:
    """List all versions for a session, newest first."""
    prefix = f"versions/{session_id}/"
    resp = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)

    versions = []
    for obj in resp.get("Contents", []):
        data = s3.get_object(Bucket=S3_BUCKET, Key=obj["Key"])
        versions.append(json.loads(data["Body"].read()))

    versions.sort(key=lambda v: v["timestamp"], reverse=True)
    return versions


def get_latest(session_id: str) -> dict:
    """Get the most recent version for a session."""
    versions = list_versions(session_id)
    return versions[0] if versions else {}


if __name__ == "__main__":
    session_id = str(uuid.uuid4())
    print(f"=== Version Management Demo ===")
    print(f"Session: {session_id}\n")

    # Save version 1
    print("--- Saving version 1 (initial) ---")
    v1 = save_version(
        session_id,
        "<html><body><h1>John Doe</h1><p>Software Engineer</p></body></html>",
    )

    # Save version 2 (with feedback)
    print("\n--- Saving version 2 (refined) ---")
    v2 = save_version(
        session_id,
        "<html><body><h1>John Doe</h1><p>Senior Software Engineer with 5+ years...</p></body></html>",
        feedback="Make the summary more detailed",
    )

    # Save version 3
    print("\n--- Saving version 3 (more changes) ---")
    v3 = save_version(
        session_id,
        "<html><body><h1>John Doe</h1><p>Senior SWE specializing in distributed systems...</p></body></html>",
        feedback="Emphasize distributed systems experience",
    )

    # List all versions
    print(f"\n--- Listing all versions ---")
    versions = list_versions(session_id)
    print(f"Found {len(versions)} versions:")
    for v in versions:
        fb = v.get("feedback") or "(initial)"
        print(f"  {v['version_id'][:8]}... | {v['timestamp']} | {fb}")

    # Get latest
    print(f"\n--- Getting latest version ---")
    latest = get_latest(session_id)
    print(f"Latest: {latest['version_id'][:8]}...")
    print(f"HTML preview: {latest['html_content'][:80]}...")

    print(f"\n✓ All versions stored in s3://{S3_BUCKET}/versions/{session_id}/")

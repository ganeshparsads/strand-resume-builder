"""
Step 1: AgentCore Entrypoint
==============================

This is the self-contained entrypoint for AgentCore deployment.
All tools are defined inline — no cross-module imports.

Why self-contained?
- AgentCore has a 30-second initialization timeout
- Importing from other modules can be slow on cold start
- Keeping everything in one file ensures fast startup

Key pattern:
- BedrockAgentCoreApp wraps your agent as an HTTP server
- @app.entrypoint marks the function that handles requests
- app.run() starts the local dev server on port 8080

To test locally:
  uv run python step1_entrypoint.py

Then in another terminal:
  curl -X POST http://localhost:8080/invocations \\
    -H "Content-Type: application/json" \\
    -d '{"prompt": "Hello, what can you do?"}'
"""

import base64
import json
import os
import time
import uuid
from datetime import datetime, timezone

import boto3
from bedrock_agentcore import BedrockAgentCoreApp
from botocore.config import Config as BotocoreConfig
from strands import Agent, tool
from strands.models.bedrock import BedrockModel

# --- App and Config ---
app = BedrockAgentCoreApp()

AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
S3_BUCKET = os.environ.get("RESUME_S3_BUCKET", "CHANGE-ME")

model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region_name=AWS_REGION,
    boto_client_config=BotocoreConfig(read_timeout=300),
)


# --- Helper for direct PDF extraction (called outside agent) ---
def _do_extract_text(pdf_base64: str) -> str:
    """Extract text from base64 PDF via Textract (plain function)."""
    pdf_bytes = base64.b64decode(pdf_base64)
    if not pdf_bytes[:5].startswith(b"%PDF"):
        raise ValueError("Not a valid PDF")

    s3 = boto3.client("s3", region_name=AWS_REGION)
    s3_key = f"uploads/{uuid.uuid4()}/resume.pdf"
    s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=pdf_bytes)

    textract = boto3.client("textract", region_name=AWS_REGION)
    resp = textract.start_document_text_detection(
        DocumentLocation={"S3Object": {"Bucket": S3_BUCKET, "Name": s3_key}}
    )
    job_id = resp["JobId"]

    while True:
        result = textract.get_document_text_detection(JobId=job_id)
        if result["JobStatus"] == "SUCCEEDED":
            break
        elif result["JobStatus"] == "FAILED":
            raise RuntimeError("Textract failed")
        time.sleep(2)

    lines, next_token = [], None
    while True:
        if next_token:
            result = textract.get_document_text_detection(JobId=job_id, NextToken=next_token)
        for block in result.get("Blocks", []):
            if block.get("BlockType") == "LINE":
                t = block.get("Text", "").strip()
                if t:
                    lines.append(t)
        next_token = result.get("NextToken")
        if not next_token:
            break

    text = "\n".join(lines)
    if not text.strip():
        raise RuntimeError("No text found in PDF")
    return text


# --- Tools (all inline for fast cold start) ---

@tool
def extract_text_from_pdf(pdf_base64: str) -> str:
    """Extract text from a base64-encoded PDF using AWS Textract.
    Args:
        pdf_base64: Base64-encoded PDF file content.
    """
    return _do_extract_text(pdf_base64)

@tool
def parse_resume(resume_text: str) -> dict:
    """Validate resume text for structured parsing.
    Args:
        resume_text: Plain text of a resume (100-50000 chars).
    """
    n = len(resume_text.strip())
    if n < 100:
        raise ValueError(f"Resume too short ({n} chars).")
    return {"status": "validated", "char_count": n}

@tool
def parse_job_description(job_description: str) -> dict:
    """Validate job description for structured parsing.
    Args:
        job_description: Plain text of a job posting (50-30000 chars).
    """
    n = len(job_description.strip())
    if n < 50:
        raise ValueError(f"JD too short ({n} chars).")
    return {"status": "validated", "char_count": n}

@tool
def match_skills(profile: dict, requirements: dict) -> dict:
    """Validate inputs for skill matching analysis.
    Args:
        profile: Dict with resume data.
        requirements: Dict with job data.
    """
    if not profile or not requirements:
        raise ValueError("Both inputs required")
    return {"status": "validated", "profile": profile, "requirements": requirements}

@tool
def generate_resume_html(profile: dict, match_result: dict, job_requirements: dict,
                         feedback: str = "", current_html: str = "") -> dict:
    """Validate inputs for ATS-friendly HTML resume generation.
    Args:
        profile: Parsed resume data.
        match_result: Skill matching results.
        job_requirements: Parsed job requirements.
        feedback: Optional refinement feedback.
        current_html: Optional existing HTML to refine.
    """
    if not profile or not match_result or not job_requirements:
        raise ValueError("profile, match_result, and job_requirements required")
    return {"status": "validated"}

@tool
def manage_versions(action: str, session_id: str, html_content: str = "",
                    version_id: str = "", feedback: str = "") -> dict:
    """Manage resume version history in S3.
    Args:
        action: One of save, get_latest, get, list.
        session_id: Session UUID.
        html_content: HTML to save (for save action).
        version_id: Version to get (for get action).
        feedback: Feedback text.
    """
    s3 = boto3.client("s3", region_name=AWS_REGION)
    prefix = f"versions/{session_id}/"
    if action == "save":
        vid = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        record = {"version_id": vid, "session_id": session_id,
                  "timestamp": ts, "html_content": html_content, "feedback": feedback or None}
        s3.put_object(Bucket=S3_BUCKET, Key=f"{prefix}{vid}.json", Body=json.dumps(record))
        return {"status": "saved", "record": record}
    elif action == "list":
        resp = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
        versions = []
        for obj in resp.get("Contents", []):
            data = s3.get_object(Bucket=S3_BUCKET, Key=obj["Key"])
            versions.append(json.loads(data["Body"].read()))
        versions.sort(key=lambda v: v["timestamp"], reverse=True)
        return {"status": "found", "count": len(versions), "versions": versions}
    elif action == "get_latest":
        resp = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
        vlist = []
        for obj in resp.get("Contents", []):
            data = s3.get_object(Bucket=S3_BUCKET, Key=obj["Key"])
            vlist.append(json.loads(data["Body"].read()))
        vlist.sort(key=lambda v: v["timestamp"], reverse=True)
        return {"status": "found", "record": vlist[0]} if vlist else {"status": "empty", "record": {}}
    elif action == "get":
        try:
            data = s3.get_object(Bucket=S3_BUCKET, Key=f"{prefix}{version_id}.json")
            return {"status": "found", "record": json.loads(data["Body"].read())}
        except Exception:
            raise ValueError(f"Version {version_id} not found")
    raise ValueError(f"Invalid action: {action}")


# --- Agent ---
SYSTEM_PROMPT = """You are a professional resume optimization agent.

Available tools: extract_text_from_pdf, parse_resume, parse_job_description,
match_skills, generate_resume_html, manage_versions

Workflow:
1. If base64 PDF provided, extract text first
2. Parse resume → structured JSON
3. Parse job description → structured JSON
4. Match skills → alignment analysis
5. Generate ATS-friendly HTML (semantic tags, no scripts)
6. Save version via manage_versions

For refinement: get latest version, apply feedback, save new version."""

agent = Agent(
    model=model,
    tools=[extract_text_from_pdf, parse_resume, parse_job_description,
           match_skills, generate_resume_html, manage_versions],
    system_prompt=SYSTEM_PROMPT,
)


@app.entrypoint
def invoke(payload):
    """AgentCore entrypoint — handles all requests."""
    user_message = payload.get("prompt", payload.get("message", ""))
    if not user_message:
        return {"error": "prompt or message is required"}

    # Pre-extract PDF to keep LLM prompt small
    pdf_marker = "Resume PDF base64:\n"
    if pdf_marker in user_message:
        parts = user_message.split(pdf_marker, 1)
        try:
            resume_text = _do_extract_text(parts[1].strip())
            user_message = f"{parts[0].strip()}\n\nExtracted Resume Text:\n{resume_text}"
        except Exception as e:
            return {"error": f"PDF extraction failed: {e}"}

    try:
        result = agent(user_message)
        return {"result": str(result)}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    app.run()

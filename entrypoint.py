"""AgentCore entrypoint — self-contained with all tools."""

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

app = BedrockAgentCoreApp()

AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
S3_BUCKET = os.environ.get(
    "RESUME_S3_BUCKET", "resume-modifier-agent-dev-CHANGEME"
)

model = BedrockModel(
    model_id=os.environ.get(
        "BEDROCK_MODEL_ID",
        "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    ),
    region_name=AWS_REGION,
    boto_client_config=BotocoreConfig(read_timeout=300),
)


# --- Tools ---

def _do_extract_text_from_pdf(pdf_base64: str) -> str:
    """Extract text from base64 PDF — plain function for direct calls."""
    pdf_bytes = base64.b64decode(pdf_base64)
    if not pdf_bytes[:5].startswith(b"%PDF"):
        raise ValueError("Not a valid PDF")
    if len(pdf_bytes) > 10 * 1024 * 1024:
        raise ValueError("PDF exceeds 10 MB limit")

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

    lines = []
    next_token = None
    while True:
        if next_token:
            result = textract.get_document_text_detection(
                JobId=job_id, NextToken=next_token
            )
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


@tool
def extract_text_from_pdf(pdf_base64: str) -> str:
    """Extract text from a base64-encoded PDF using AWS Textract async API.

    Args:
        pdf_base64: Base64-encoded PDF file content.

    Returns:
        Plain text extracted from the PDF.
    """
    return _do_extract_text_from_pdf(pdf_base64)


@tool
def parse_resume(resume_text: str) -> dict:
    """Validate resume text for structured parsing.

    Args:
        resume_text: Plain text of a resume (100-50000 chars).
    """
    n = len(resume_text.strip())
    if n < 100:
        raise ValueError(f"Resume too short ({n} chars). Min 100.")
    if n > 50_000:
        raise ValueError(f"Resume too long ({n} chars). Max 50000.")
    return {"status": "validated", "char_count": n}


@tool
def parse_job_description(job_description: str) -> dict:
    """Validate job description for structured parsing.

    Args:
        job_description: Plain text of a job posting (50-30000 chars).
    """
    n = len(job_description.strip())
    if n < 50:
        raise ValueError(f"JD too short ({n} chars). Min 50.")
    if n > 30_000:
        raise ValueError(f"JD too long ({n} chars). Max 30000.")
    return {"status": "validated", "char_count": n}


@tool
def match_skills(profile: dict, requirements: dict) -> dict:
    """Validate inputs for skill matching analysis.

    Args:
        profile: Dict conforming to ResumeProfile schema.
        requirements: Dict conforming to JobRequirements schema.
    """
    if not profile or not isinstance(profile, dict):
        raise ValueError("profile must be a non-empty dict")
    if not requirements or not isinstance(requirements, dict):
        raise ValueError("requirements must be a non-empty dict")
    return {"status": "validated", "profile": profile, "requirements": requirements}


@tool
def generate_resume_html(
    profile: dict,
    match_result: dict,
    job_requirements: dict,
    feedback: str = "",
    current_html: str = "",
) -> dict:
    """Validate inputs for ATS-friendly HTML resume generation.

    Args:
        profile: Dict conforming to ResumeProfile schema.
        match_result: Dict conforming to SkillMatchResult schema.
        job_requirements: Dict conforming to JobRequirements schema.
        feedback: Optional refinement feedback.
        current_html: Optional current HTML to refine.
    """
    if not profile:
        raise ValueError("profile required")
    if not match_result:
        raise ValueError("match_result required")
    if not job_requirements:
        raise ValueError("job_requirements required")
    if feedback and not current_html:
        raise ValueError("current_html required when feedback provided")
    return {"status": "validated"}


@tool
def manage_versions(
    action: str,
    session_id: str,
    html_content: str = "",
    version_id: str = "",
    feedback: str = "",
) -> dict:
    """Manage resume version history in S3.

    Args:
        action: One of save, get_latest, get, list.
        session_id: Session UUID.
        html_content: HTML to save (required for save).
        version_id: Version to retrieve (required for get).
        feedback: Feedback that produced this version.
    """
    s3 = boto3.client("s3", region_name=AWS_REGION)
    prefix = f"versions/{session_id}/"

    if action == "save":
        if not html_content:
            raise ValueError("html_content required for save")
        vid = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        record = {
            "version_id": vid, "session_id": session_id,
            "timestamp": ts, "html_content": html_content,
            "feedback": feedback or None,
        }
        s3.put_object(
            Bucket=S3_BUCKET, Key=f"{prefix}{vid}.json",
            Body=json.dumps(record),
        )
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
        versions_list = []
        for obj in resp.get("Contents", []):
            data = s3.get_object(Bucket=S3_BUCKET, Key=obj["Key"])
            versions_list.append(json.loads(data["Body"].read()))
        versions_list.sort(key=lambda v: v["timestamp"], reverse=True)
        return {"status": "found", "record": versions_list[0]} if versions_list else {"status": "empty", "record": {}}

    elif action == "get":
        key = f"{prefix}{version_id}.json"
        try:
            data = s3.get_object(Bucket=S3_BUCKET, Key=key)
            return {"status": "found", "record": json.loads(data["Body"].read())}
        except Exception:
            raise ValueError(f"Version {version_id} not found")

    raise ValueError(f"Invalid action: {action}")


# --- Agent ---

SYSTEM_PROMPT = """You are a professional resume optimization agent.
You help users create tailored, ATS-friendly resumes.

Available tools:
- extract_text_from_pdf: Extract text from base64-encoded PDF via Textract
- parse_resume: Validate resume text for parsing
- parse_job_description: Validate job description text for parsing
- match_skills: Validate inputs for skill matching
- generate_resume_html: Validate inputs for HTML generation
- manage_versions: Save/retrieve resume versions in S3

Full workflow:
1. If user provides a base64 PDF, call extract_text_from_pdf first
2. Call parse_resume with the text, then produce structured JSON
3. Call parse_job_description, then produce structured JSON
4. Call match_skills, then produce skill alignment analysis
5. Generate ATS-friendly HTML resume with semantic tags
6. Call manage_versions to save the version

Use semantic HTML (section, h1-h3, ul, li). No script tags.
For refinement: get latest version, apply feedback, save new version."""

agent = Agent(
    model=model,
    tools=[
        extract_text_from_pdf, parse_resume, parse_job_description,
        match_skills, generate_resume_html, manage_versions,
    ],
    system_prompt=SYSTEM_PROMPT,
)


@app.entrypoint
def invoke(payload):
    """Process user input and return a response."""
    user_message = payload.get("prompt", payload.get("message", ""))
    if not user_message:
        return {"error": "prompt or message is required"}

    # If prompt contains base64 PDF, extract text first to keep the LLM prompt small
    pdf_marker = "Resume PDF base64:\n"
    if pdf_marker in user_message:
        parts = user_message.split(pdf_marker, 1)
        prompt_text = parts[0].strip()
        pdf_b64 = parts[1].strip()
        try:
            resume_text = _do_extract_text_from_pdf(pdf_b64)
            user_message = f"{prompt_text}\n\nExtracted Resume Text:\n{resume_text}"
        except Exception as e:
            return {"error": f"PDF extraction failed: {e}"}

    try:
        result = agent(user_message)
        return {"result": str(result)}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    app.run()

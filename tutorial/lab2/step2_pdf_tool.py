"""
Step 2: PDF Extraction as an Agent Tool
=========================================

Now we wrap the Textract logic from Step 1 into a @tool so the
agent can call it. We also add the job description parser.

The agent now has 3 tools:
- extract_text_from_pdf: Reads base64 PDF → Textract → plain text
- parse_resume: Validates resume text
- parse_job_description: Validates job description text

Why base64? When deployed to AgentCore, the frontend sends the PDF
as a base64-encoded string in the JSON payload. We use the same
format locally for consistency.

Run: uv run python step2_pdf_tool.py
"""

import base64
import os
import time
import uuid

import boto3
from strands import Agent, tool
from strands.models.bedrock import BedrockModel

AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
S3_BUCKET = os.environ.get("RESUME_S3_BUCKET")

if not S3_BUCKET:
    print("ERROR: Set RESUME_S3_BUCKET first. Run setup.sh.")
    exit(1)

model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region_name=AWS_REGION,
)


# --- Tool 1: PDF Text Extraction ---
@tool
def extract_text_from_pdf(pdf_base64: str) -> str:
    """Extract text from a base64-encoded PDF using AWS Textract.

    Use this when the user provides a PDF resume. The PDF must be
    base64-encoded. Returns plain text extracted from all pages.

    Args:
        pdf_base64: Base64-encoded PDF file content.

    Returns:
        Plain text extracted from the PDF.
    """
    print("  [Tool] extract_text_from_pdf called")

    # Decode base64 to bytes
    pdf_bytes = base64.b64decode(pdf_base64)
    if not pdf_bytes[:5].startswith(b"%PDF"):
        raise ValueError("Not a valid PDF")

    # Upload to S3
    s3 = boto3.client("s3", region_name=AWS_REGION)
    s3_key = f"uploads/{uuid.uuid4()}/resume.pdf"
    s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=pdf_bytes)
    print(f"  [Tool] Uploaded to S3: {s3_key}")

    # Async Textract
    textract = boto3.client("textract", region_name=AWS_REGION)
    resp = textract.start_document_text_detection(
        DocumentLocation={"S3Object": {"Bucket": S3_BUCKET, "Name": s3_key}}
    )
    job_id = resp["JobId"]
    print(f"  [Tool] Textract job: {job_id}")

    # Poll
    while True:
        result = textract.get_document_text_detection(JobId=job_id)
        if result["JobStatus"] == "SUCCEEDED":
            break
        elif result["JobStatus"] == "FAILED":
            raise RuntimeError("Textract failed")
        time.sleep(2)

    # Collect lines
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
    print(f"  [Tool] Extracted {len(lines)} lines")
    return text


# --- Tool 2: Resume Validator ---
@tool
def parse_resume(resume_text: str) -> dict:
    """Validate resume text for structured parsing.

    Args:
        resume_text: Plain text content of a resume (100-50000 chars).
    """
    n = len(resume_text.strip())
    if n < 100:
        raise ValueError(f"Resume too short ({n} chars). Min 100.")
    print(f"  [Tool] parse_resume — {n} chars ✓")
    return {"status": "validated", "char_count": n}


# --- Tool 3: Job Description Validator ---
@tool
def parse_job_description(job_description: str) -> dict:
    """Validate job description for structured parsing.

    Args:
        job_description: Plain text of a job posting (50-30000 chars).
    """
    n = len(job_description.strip())
    if n < 50:
        raise ValueError(f"JD too short ({n} chars). Min 50.")
    print(f"  [Tool] parse_job_description — {n} chars ✓")
    return {"status": "validated", "char_count": n}


# --- Agent with all 3 tools ---
agent = Agent(
    model=model,
    tools=[extract_text_from_pdf, parse_resume, parse_job_description],
    system_prompt="""You are a resume optimization agent.

Available tools:
- extract_text_from_pdf: Extract text from base64-encoded PDF
- parse_resume: Validate resume text
- parse_job_description: Validate job description text

Workflow:
1. If given a base64 PDF, call extract_text_from_pdf first
2. Call parse_resume with the extracted text
3. Parse the job description with parse_job_description
4. Extract structured JSON for both
Only extract information present in the text.""",
)


# --- Test ---
if __name__ == "__main__":
    pdf_path = "resume.pdf"
    if not os.path.exists(pdf_path):
        print(f"Place a '{pdf_path}' file in this directory first.")
        exit(1)

    # Read PDF and encode as base64
    with open(pdf_path, "rb") as f:
        pdf_b64 = base64.b64encode(f.read()).decode()

    JOB_DESC = """
    Senior Software Engineer - Amazon
    Required: Python, Java, AWS, Distributed Systems, Docker, Kubernetes
    Preferred: ML experience, Kafka, Spark, CI/CD pipelines
    Responsibilities: Design ML pipelines, optimize systems, mentor engineers
    Qualifications: MS in Computer Science, 5+ years experience
    """

    print("Sending PDF resume + job description to agent...\n")
    print("(This may take 30-60 seconds for Textract processing)\n")

    # Pre-extract PDF to keep prompt small
    print("Step 1: Extracting PDF text via Textract...")
    resume_text = extract_text_from_pdf.tool_func(pdf_base64=pdf_b64)
    print(f"Extracted {len(resume_text)} chars\n")

    print("Step 2: Sending to agent for parsing...\n")
    response = agent(
        f"Parse this resume and job description into structured JSON.\n\n"
        f"Resume:\n{resume_text}\n\n"
        f"Job Description:\n{JOB_DESC}"
    )
    print(f"\n--- Agent Response (first 1000 chars) ---\n")
    print(str(response)[:1000])

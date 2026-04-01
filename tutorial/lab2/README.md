# Lab 2: PDF Extraction with AWS Textract + Job Description Parsing

## Objective
Extend the agent with PDF resume support using AWS Textract and add job description parsing. By the end, your agent can read PDF resumes and analyze job postings.

## Prerequisites
- Completed Lab 1
- S3 bucket for Textract (we'll create one)
- Bedrock and Textract permissions on your AWS role

## Step 1: Create an S3 Bucket

Textract's async API needs PDFs in S3. Create a dev bucket:

```bash
aws s3 mb s3://resume-agent-dev-$(aws sts get-caller-identity --query Account --output text) --region us-east-1
```

Set the bucket name as an environment variable:
```bash
export RESUME_S3_BUCKET=resume-agent-dev-<your-account-id>
```

## Step 2: Add the PDF Extraction Tool

Update `agent.py` to add the `extract_text_from_pdf` tool:

```python
import base64
import os
import time
import uuid

import boto3
from strands import Agent, tool
from strands.models.bedrock import BedrockModel

AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
S3_BUCKET = os.environ.get("RESUME_S3_BUCKET", "resume-agent-dev-CHANGEME")

model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region_name=AWS_REGION,
)


@tool
def extract_text_from_pdf(pdf_base64: str) -> str:
    """Extract text from a base64-encoded PDF using AWS Textract.

    Args:
        pdf_base64: Base64-encoded PDF file content.

    Returns:
        Plain text extracted from the PDF.
    """
    # Decode and validate
    pdf_bytes = base64.b64decode(pdf_base64)
    if not pdf_bytes[:5].startswith(b"%PDF"):
        raise ValueError("Not a valid PDF")
    if len(pdf_bytes) > 10 * 1024 * 1024:
        raise ValueError("PDF exceeds 10 MB limit")

    # Upload to S3 (Textract async API requires S3)
    s3 = boto3.client("s3", region_name=AWS_REGION)
    s3_key = f"uploads/{uuid.uuid4()}/resume.pdf"
    s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=pdf_bytes)

    # Start async text detection (supports multi-page PDFs)
    textract = boto3.client("textract", region_name=AWS_REGION)
    resp = textract.start_document_text_detection(
        DocumentLocation={"S3Object": {"Bucket": S3_BUCKET, "Name": s3_key}}
    )
    job_id = resp["JobId"]

    # Poll until complete
    while True:
        result = textract.get_document_text_detection(JobId=job_id)
        if result["JobStatus"] == "SUCCEEDED":
            break
        elif result["JobStatus"] == "FAILED":
            raise RuntimeError("Textract failed")
        time.sleep(2)

    # Collect text from all pages
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
```

### Why Async Textract?
Textract's synchronous `DetectDocumentText` with raw bytes only supports single-page documents. Most resumes are 2-4 pages, so we use the async `StartDocumentTextDetection` API which requires S3.

## Step 3: Add Job Description Parser

Add a second tool for parsing job descriptions:

```python
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
```

## Step 4: Wire Tools into the Agent

```python
agent = Agent(
    model=model,
    tools=[extract_text_from_pdf, parse_resume, parse_job_description],
    system_prompt="""You are a resume optimization agent.

Available tools:
- extract_text_from_pdf: Extract text from base64-encoded PDF
- parse_resume: Validate resume text
- parse_job_description: Validate job description text

Workflow:
1. If given a PDF, extract text first
2. Parse the resume into structured JSON
3. Parse the job description into structured JSON
Only extract information present in the text.""",
)
```

## Step 5: Test with a Real PDF

Create `test_pdf.py`:

```python
import base64
from agent import agent

# Read a local PDF and encode as base64
with open("resume.pdf", "rb") as f:
    pdf_b64 = base64.b64encode(f.read()).decode()

JOB_DESC = """
Senior Software Engineer - Amazon
Required: Python, Java, AWS, Distributed Systems, Docker
Preferred: ML experience, Kafka, CI/CD
Responsibilities: Design ML pipelines, mentor engineers
Qualifications: MS CS, 5+ years experience
"""

response = agent(
    f"Extract text from this PDF resume and parse both the resume "
    f"and this job description:\n\n"
    f"Job Description:\n{JOB_DESC}\n\n"
    f"Resume PDF (base64):\n{pdf_b64}"
)
print(response)
```

> **Note:** Place a `resume.pdf` file in your project directory before running.

```bash
uv run python test_pdf.py
```

## What You Learned
- How to use AWS Textract for PDF text extraction
- Why async Textract is needed for multi-page PDFs
- How to chain multiple tools in a single agent
- How the agent orchestrates tool calls based on input

## Next: Lab 3
In Lab 3, you'll add skill matching, HTML resume generation, and version management.

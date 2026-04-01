"""Tool for extracting text from PDF resumes using AWS Textract.

Uses S3 + async Textract API to support multi-page PDFs.
"""

import os
import time
import uuid

import boto3
from strands import tool

S3_BUCKET = os.environ.get(
    "RESUME_S3_BUCKET", "resume-modifier-agent-dev-CHANGEME"
)
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB


def _read_and_validate_pdf(file_path: str) -> bytes:
    """Read a local PDF file and validate it."""
    if not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")
    if not file_path.lower().endswith(".pdf"):
        raise ValueError("File must be a .pdf file")

    with open(file_path, "rb") as f:
        pdf_bytes = f.read()

    if not pdf_bytes[:5].startswith(b"%PDF"):
        raise ValueError("Uploaded file is not a valid PDF")
    if len(pdf_bytes) > MAX_PDF_SIZE:
        size_mb = len(pdf_bytes) / (1024 * 1024)
        raise ValueError(
            f"PDF exceeds maximum size of 10 MB (got {size_mb:.1f} MB)"
        )
    return pdf_bytes


def _upload_to_s3(pdf_bytes: bytes) -> str:
    """Upload PDF to S3 and return the S3 key."""
    s3 = boto3.client("s3", region_name=AWS_REGION)
    s3_key = f"uploads/{uuid.uuid4()}/resume.pdf"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=pdf_bytes,
        ContentType="application/pdf",
    )
    return s3_key


def _extract_text_via_textract(s3_key: str) -> str:
    """Use async Textract API for multi-page PDF support."""
    textract = boto3.client("textract", region_name=AWS_REGION)

    # Start async text detection
    response = textract.start_document_text_detection(
        DocumentLocation={
            "S3Object": {"Bucket": S3_BUCKET, "Name": s3_key}
        }
    )
    job_id = response["JobId"]

    # Poll until complete
    while True:
        result = textract.get_document_text_detection(JobId=job_id)
        status = result["JobStatus"]
        if status == "SUCCEEDED":
            break
        elif status == "FAILED":
            raise RuntimeError(
                f"Textract job failed: {result.get('StatusMessage', 'Unknown error')}"
            )
        time.sleep(2)

    # Collect all pages
    lines = []
    next_token = None
    while True:
        if next_token:
            result = textract.get_document_text_detection(
                JobId=job_id, NextToken=next_token
            )
        for block in result.get("Blocks", []):
            if block.get("BlockType") == "LINE":
                text = block.get("Text", "").strip()
                if text:
                    lines.append(text)
        next_token = result.get("NextToken")
        if not next_token:
            break

    extracted_text = "\n".join(lines)
    if not extracted_text.strip():
        raise RuntimeError("No text content found in PDF")
    return extracted_text


@tool
def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a local PDF resume using AWS Textract.

    Reads the PDF from a local file path, uploads to S3, and uses
    Textract async API to extract text from all pages.

    Args:
        file_path: Local path to the PDF file (e.g. "resume.pdf").

    Returns:
        Plain text extracted from the PDF, lines joined by newlines.
    """
    if not file_path or not isinstance(file_path, str):
        raise ValueError("file_path must be a non-empty string")

    pdf_bytes = _read_and_validate_pdf(file_path)
    s3_key = _upload_to_s3(pdf_bytes)
    extracted_text = _extract_text_via_textract(s3_key)
    return extracted_text

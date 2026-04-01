"""
Step 1: Textract Basics — Extracting Text from PDFs
=====================================================

AWS Textract is a service that extracts text from documents.
Before wiring it into our agent, let's understand how it works.

Two Textract APIs:
- DetectDocumentText (sync): Single-page only, accepts raw bytes
- StartDocumentTextDetection (async): Multi-page, requires S3

Most resumes are 2-4 pages, so we use the async API.

Flow: Local PDF → Upload to S3 → Textract reads from S3 → Poll for results

Prerequisites:
- S3 bucket created (run setup.sh first)
- Set RESUME_S3_BUCKET environment variable
- Place a resume.pdf in this directory

Run: uv run python step1_textract_basics.py
"""

import os
import time
import uuid

import boto3

AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
S3_BUCKET = os.environ.get("RESUME_S3_BUCKET")

if not S3_BUCKET:
    print("ERROR: Set RESUME_S3_BUCKET environment variable first.")
    print("Run: export RESUME_S3_BUCKET=resume-agent-dev-<your-account-id>")
    exit(1)


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a local PDF using Textract async API."""

    # --- Step 1: Read and validate the PDF ---
    print(f"Reading {file_path}...")
    with open(file_path, "rb") as f:
        pdf_bytes = f.read()

    # Check PDF magic bytes (every PDF starts with %PDF)
    if not pdf_bytes[:5].startswith(b"%PDF"):
        raise ValueError("Not a valid PDF file")

    size_mb = len(pdf_bytes) / (1024 * 1024)
    print(f"  Size: {size_mb:.1f} MB")

    # --- Step 2: Upload to S3 ---
    # Textract async API can only read from S3, not raw bytes
    s3 = boto3.client("s3", region_name=AWS_REGION)
    s3_key = f"uploads/{uuid.uuid4()}/resume.pdf"
    print(f"  Uploading to s3://{S3_BUCKET}/{s3_key}...")
    s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=pdf_bytes)

    # --- Step 3: Start async text detection ---
    textract = boto3.client("textract", region_name=AWS_REGION)
    print("  Starting Textract job...")
    response = textract.start_document_text_detection(
        DocumentLocation={
            "S3Object": {"Bucket": S3_BUCKET, "Name": s3_key}
        }
    )
    job_id = response["JobId"]
    print(f"  Job ID: {job_id}")

    # --- Step 4: Poll until complete ---
    print("  Waiting for Textract to finish", end="")
    while True:
        result = textract.get_document_text_detection(JobId=job_id)
        status = result["JobStatus"]
        if status == "SUCCEEDED":
            print(" Done!")
            break
        elif status == "FAILED":
            raise RuntimeError("Textract job failed")
        print(".", end="", flush=True)
        time.sleep(2)

    # --- Step 5: Collect text from all pages ---
    # Textract returns "Blocks" — we want LINE blocks in reading order
    lines = []
    next_token = None
    page_count = 0

    while True:
        if next_token:
            result = textract.get_document_text_detection(
                JobId=job_id, NextToken=next_token
            )

        for block in result.get("Blocks", []):
            if block["BlockType"] == "PAGE":
                page_count += 1
            elif block["BlockType"] == "LINE":
                text = block.get("Text", "").strip()
                if text:
                    lines.append(text)

        next_token = result.get("NextToken")
        if not next_token:
            break

    print(f"  Pages: {page_count}")
    print(f"  Lines extracted: {len(lines)}")

    return "\n".join(lines)


# --- Run it ---
if __name__ == "__main__":
    # Check for a PDF file
    pdf_path = "resume.pdf"
    if not os.path.exists(pdf_path):
        print(f"Place a '{pdf_path}' file in this directory first.")
        exit(1)

    text = extract_text_from_pdf(pdf_path)
    print(f"\n--- Extracted Text (first 500 chars) ---\n")
    print(text[:500])
    print(f"\n... ({len(text)} total characters)")

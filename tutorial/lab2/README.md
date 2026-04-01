# Lab 2: PDF Extraction with AWS Textract + Job Description Parsing

## Overview
Extend the agent with PDF resume support using AWS Textract and add job description parsing.

| Step | File | What You Learn |
|------|------|----------------|
| Setup | `setup.sh` | Create S3 bucket for Textract |
| 1 | `step1_textract_basics.py` | How Textract works: upload → detect → poll → collect |
| 2 | `step2_pdf_tool.py` | Wrap Textract as a @tool, add JD parser, 3-tool agent |

## Prerequisites
- Completed Lab 1
- AWS credentials with S3 and Textract permissions
- A `resume.pdf` file in this directory

## Quick Start

```bash
cd tutorial/lab2
chmod +x setup.sh
./setup.sh
export RESUME_S3_BUCKET=resume-agent-dev-<your-account-id>

# Copy a resume PDF here
cp /path/to/your/resume.pdf .

uv run python step1_textract_basics.py
uv run python step2_pdf_tool.py
```

## Step-by-Step Guide

### Step 1: Textract Basics (`step1_textract_basics.py`)

Before wiring Textract into the agent, understand the raw API:

1. Read local PDF and validate magic bytes (`%PDF`)
2. Upload to S3 (Textract async API requires S3)
3. Call `start_document_text_detection` — returns a Job ID
4. Poll `get_document_text_detection` until status is `SUCCEEDED`
5. Collect `LINE` blocks from all pages in reading order

Why async? Textract's sync API (`DetectDocumentText` with bytes) only supports single-page documents. Resumes are typically 2-4 pages.

### Step 2: PDF as Agent Tool (`step2_pdf_tool.py`)

Wraps the Textract logic into a `@tool` and adds a job description parser. The agent now has 3 tools and can:
- Accept a base64-encoded PDF
- Extract text via Textract
- Parse both resume and job description into structured JSON

Key pattern: we pre-extract the PDF text before sending to the agent to keep the LLM prompt small (base64 PDFs are huge).

## Key Concepts

| Concept | Why It Matters |
|---------|---------------|
| Async Textract | Supports multi-page PDFs (sync only does 1 page) |
| S3 upload | Required by Textract async API |
| Base64 encoding | Standard way to send binary files in JSON payloads |
| Pre-extraction | Extract PDF text before LLM call to avoid huge prompts |

## Next: Lab 3
In Lab 3, you'll add skill matching, HTML resume generation, and version management.

"""Strands Agent for Resume Modification.

Configures the agent with Bedrock model and resume processing tools.
"""

import os
from strands import Agent
from strands.models.bedrock import BedrockModel

from src.tools.parse_resume import parse_resume
from src.tools.extract_text_from_pdf import extract_text_from_pdf

SYSTEM_PROMPT = """You are a professional resume optimization agent.
You help users create tailored, ATS-friendly resumes by analyzing
their profile against job descriptions.

You have access to these tools:
- extract_text_from_pdf: Extract text from a PDF resume via AWS Textract
- parse_resume: Validate resume text for structured parsing

Workflow for resume parsing:
1. If the user provides a base64-encoded PDF, call extract_text_from_pdf first
2. Then call parse_resume with the extracted text
3. After parse_resume validates the text, produce a structured JSON response
   with these fields: name, email, phone, summary, skills, experience,
   education, certifications, projects
4. Only extract information present in the resume — do not fabricate

Return the structured resume data as JSON in your response."""

MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID",
    "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
)
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


def create_agent() -> Agent:
    """Create and return a configured Strands agent."""
    model = BedrockModel(
        model_id=MODEL_ID,
        region_name=AWS_REGION,
    )
    return Agent(
        model=model,
        tools=[extract_text_from_pdf, parse_resume],
        system_prompt=SYSTEM_PROMPT,
    )

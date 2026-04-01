"""Strands Agent for Resume Modification.

Configures the agent with Bedrock model and all resume processing tools.
"""

import os
from strands import Agent
from strands.models.bedrock import BedrockModel

from src.tools.extract_text_from_pdf import extract_text_from_pdf
from src.tools.parse_resume import parse_resume
from src.tools.parse_job_description import parse_job_description
from src.tools.match_skills import match_skills
from src.tools.generate_resume_html import generate_resume_html
from src.tools.manage_versions import manage_versions

SYSTEM_PROMPT = """You are a professional resume optimization agent.
You help users create tailored, ATS-friendly resumes by analyzing
their profile against job descriptions.

Available tools:
- extract_text_from_pdf: Extract text from a local PDF resume
- parse_resume: Validate resume text for structured parsing
- parse_job_description: Validate job description for parsing
- match_skills: Analyze skill alignment between resume and job
- generate_resume_html: Generate ATS-friendly HTML resume
- manage_versions: Save/retrieve resume versions

Full workflow:
1. Extract text from PDF using extract_text_from_pdf
2. Parse resume text using parse_resume, then produce structured JSON
3. Parse job description using parse_job_description, then produce JSON
4. Match skills using match_skills, then produce alignment analysis
5. Generate HTML resume using generate_resume_html
6. Save the version using manage_versions

For refinement: get latest version, apply feedback, save new version.
Always use semantic HTML (section, h1-h3, ul, li) for ATS compatibility.
No script tags or external resources in generated HTML.
Return the final HTML resume in your response."""

MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID",
    "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
)
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


def create_agent() -> Agent:
    """Create and return a configured Strands agent with all tools."""
    model = BedrockModel(
        model_id=MODEL_ID,
        region_name=AWS_REGION,
    )
    return Agent(
        model=model,
        tools=[
            extract_text_from_pdf,
            parse_resume,
            parse_job_description,
            match_skills,
            generate_resume_html,
            manage_versions,
        ],
        system_prompt=SYSTEM_PROMPT,
    )

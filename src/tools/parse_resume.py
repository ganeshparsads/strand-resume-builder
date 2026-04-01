"""Tool for parsing raw resume text into a structured ResumeProfile.

The agent's LLM handles the actual extraction. This tool validates input
and returns the text for the agent to parse into structured JSON.
"""

import json
from strands import tool


@tool
def parse_resume(resume_text: str) -> dict:
    """Parse raw resume text into a structured ResumeProfile.

    Validates the resume text and returns it for structured extraction.
    The agent should call this tool with resume text and then produce
    a JSON object with these fields:
    - name (str, required, non-empty)
    - email (str)
    - phone (str)
    - summary (str)
    - skills (list[str], at least one entry)
    - experience (list of {company, title, start_date, end_date, bullets})
    - education (list of {institution, degree, field_of_study, graduation_date})
    - certifications (list[str])
    - projects (list of {name, description, technologies})

    Experience entries must be ordered by date descending (most recent first).
    Only extract information present in the text — do not fabricate.

    Args:
        resume_text: Plain text content of a resume (100-50,000 chars).

    Returns:
        A dict with the validated resume text ready for parsing.
    """
    if not resume_text or not isinstance(resume_text, str):
        raise ValueError("resume_text must be a non-empty string")

    text_len = len(resume_text.strip())
    if text_len < 100:
        raise ValueError(
            f"Resume text too short ({text_len} chars). Minimum 100 characters."
        )
    if text_len > 50_000:
        raise ValueError(
            f"Resume text too long ({text_len} chars). Maximum 50,000 characters."
        )

    return {
        "status": "validated",
        "resume_text": resume_text.strip(),
        "char_count": text_len,
        "instructions": (
            "Parse this resume text into a structured JSON with fields: "
            "name, email, phone, summary, skills, experience, education, "
            "certifications, projects. Order experience by date descending."
        ),
    }

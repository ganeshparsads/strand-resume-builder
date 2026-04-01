"""Tool for parsing job descriptions into structured JobRequirements."""

from strands import tool


@tool
def parse_job_description(job_description: str) -> dict:
    """Parse a job posting into structured JobRequirements.

    Validates the job description text for structured extraction.
    The agent should produce a JSON object with these fields:
    - title (str)
    - company (str)
    - required_skills (list[str], at least one entry)
    - preferred_skills (list[str])
    - responsibilities (list[str])
    - qualifications (list[str])
    - keywords (list[str], ATS-relevant terms)

    Only extract requirements present in the text — do not fabricate.

    Args:
        job_description: Plain text of a job posting (50-30,000 chars).

    Returns:
        A dict with the validated job description text ready for parsing.
    """
    if not job_description or not isinstance(job_description, str):
        raise ValueError("job_description must be a non-empty string")

    text_len = len(job_description.strip())
    if text_len < 50:
        raise ValueError(
            f"Job description too short ({text_len} chars). Minimum 50."
        )
    if text_len > 30_000:
        raise ValueError(
            f"Job description too long ({text_len} chars). Maximum 30,000."
        )

    return {
        "status": "validated",
        "job_description": job_description.strip(),
        "char_count": text_len,
        "instructions": (
            "Parse this job description into structured JSON with fields: "
            "title, company, required_skills, preferred_skills, "
            "responsibilities, qualifications, keywords. "
            "Only extract what is present — do not fabricate."
        ),
    }

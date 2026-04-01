"""Tool for generating ATS-friendly HTML resumes."""

from strands import tool


@tool
def generate_resume_html(
    profile: dict,
    match_result: dict,
    job_requirements: dict,
    feedback: str = "",
    current_html: str = "",
) -> dict:
    """Generate or refine an ATS-friendly HTML resume.

    On first call (no current_html): generates a new resume from scratch.
    On refinement (current_html provided): applies feedback to improve it.

    The agent should produce a complete HTML document using:
    - Semantic tags: section, h1-h3, ul, li for ATS compatibility
    - No script tags or external resource references
    - All matched_skills must appear in the output
    - Inline CSS only for styling
    - If feedback + current_html provided, preserve factual info
      (name, dates, companies) unless feedback says otherwise

    Args:
        profile: Dict conforming to ResumeProfile schema.
        match_result: Dict conforming to SkillMatchResult schema.
        job_requirements: Dict conforming to JobRequirements schema.
        feedback: Optional refinement feedback text.
        current_html: Optional current HTML resume to refine.

    Returns:
        A dict with inputs ready for HTML generation.
    """
    if not profile or not isinstance(profile, dict):
        raise ValueError("profile must be a non-empty dict")
    if not match_result or not isinstance(match_result, dict):
        raise ValueError("match_result must be a non-empty dict")
    if not job_requirements or not isinstance(job_requirements, dict):
        raise ValueError("job_requirements must be a non-empty dict")
    if feedback and not current_html:
        raise ValueError(
            "current_html is required when feedback is provided"
        )

    return {
        "status": "validated",
        "profile": profile,
        "match_result": match_result,
        "job_requirements": job_requirements,
        "feedback": feedback or None,
        "current_html": current_html or None,
    }

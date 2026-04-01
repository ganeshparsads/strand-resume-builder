"""Tool for analyzing skill alignment between resume and job requirements."""

from strands import tool


@tool
def match_skills(profile: dict, requirements: dict) -> dict:
    """Analyze alignment between a candidate's profile and job requirements.

    Classifies every required skill as matched or missing, identifies
    transferable skills, computes keyword coverage, and produces
    recommendations for resume optimization.

    The agent should return a JSON object with:
    - matched_skills (list[str]): skills the candidate has
    - missing_skills (list[str]): required skills the candidate lacks
    - transferable_skills (list[str]): candidate skills mappable to required
    - keyword_coverage (float): 0.0 to 1.0
    - recommendations (list[str]): suggestions for emphasis/reframing

    Invariants:
    - matched_skills ∪ missing_skills = required_skills
    - matched_skills ∩ missing_skills = ∅
    - 0.0 <= keyword_coverage <= 1.0
    - recommendations is non-empty

    Args:
        profile: Dict conforming to ResumeProfile schema.
        requirements: Dict conforming to JobRequirements schema.

    Returns:
        A dict with profile and requirements ready for skill matching.
    """
    if not profile or not isinstance(profile, dict):
        raise ValueError("profile must be a non-empty dict")
    if not requirements or not isinstance(requirements, dict):
        raise ValueError("requirements must be a non-empty dict")

    return {
        "status": "validated",
        "profile": profile,
        "requirements": requirements,
        "instructions": (
            "Analyze skill alignment. Classify every required_skill as "
            "matched or missing. Identify transferable skills. Compute "
            "keyword_coverage as a float in [0.0, 1.0]. Produce at least "
            "one recommendation. Return structured JSON with: "
            "matched_skills, missing_skills, transferable_skills, "
            "keyword_coverage, recommendations."
        ),
    }

"""Data models for the Resume Modifier Agent."""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class ExperienceEntry:
    company: str
    title: str
    start_date: str
    end_date: str  # "Present" if current
    bullets: list[str]


@dataclass
class EducationEntry:
    institution: str
    degree: str
    field_of_study: str
    graduation_date: str


@dataclass
class ProjectEntry:
    name: str
    description: str
    technologies: list[str]


@dataclass
class ResumeProfile:
    name: str
    email: str
    phone: str
    summary: str
    skills: list[str]
    experience: list[ExperienceEntry]
    education: list[EducationEntry]
    certifications: list[str] = field(default_factory=list)
    projects: list[ProjectEntry] = field(default_factory=list)


@dataclass
class JobRequirements:
    title: str
    company: str
    required_skills: list[str]
    preferred_skills: list[str]
    responsibilities: list[str]
    qualifications: list[str]
    keywords: list[str]


@dataclass
class SkillMatchResult:
    matched_skills: list[str]
    missing_skills: list[str]
    transferable_skills: list[str]
    keyword_coverage: float  # 0.0 to 1.0
    recommendations: list[str]


@dataclass
class VersionRecord:
    version_id: str
    session_id: str
    timestamp: str  # ISO 8601
    html_content: str
    feedback: str | None = None
    parent_version_id: str | None = None


# --- Validation helpers ---

def validate_session_id(session_id: str) -> bool:
    """Check that session_id is a valid UUID."""
    try:
        UUID(session_id)
        return True
    except (ValueError, AttributeError):
        return False


def validate_keyword_coverage(coverage: float) -> bool:
    """Check that keyword_coverage is in [0.0, 1.0]."""
    return isinstance(coverage, (int, float)) and 0.0 <= coverage <= 1.0


def validate_html_content(html_content: str) -> bool:
    """Check that html_content is non-empty."""
    return isinstance(html_content, str) and len(html_content.strip()) > 0

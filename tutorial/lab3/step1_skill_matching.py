"""
Step 1: Skill Matching Tool
=============================

The skill matching tool takes a parsed resume profile and job
requirements, then the agent analyzes alignment between them.

The tool itself just validates inputs — the LLM does the
intelligent matching (identifying matched/missing/transferable skills,
computing keyword coverage, generating recommendations).

This pattern — tool validates, LLM reasons — is central to Strands.
Tools handle I/O and validation. The model handles intelligence.

Run: uv run python step1_skill_matching.py
"""

import os
from strands import Agent, tool
from strands.models.bedrock import BedrockModel

model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
)


@tool
def parse_resume(resume_text: str) -> dict:
    """Validate resume text for structured parsing.
    Args:
        resume_text: Plain text content of a resume (100-50000 chars).
    """
    n = len(resume_text.strip())
    if n < 100:
        raise ValueError(f"Resume too short ({n} chars).")
    print(f"  [Tool] parse_resume — {n} chars ✓")
    return {"status": "validated", "char_count": n}


@tool
def parse_job_description(job_description: str) -> dict:
    """Validate job description for structured parsing.
    Args:
        job_description: Plain text of a job posting (50-30000 chars).
    """
    n = len(job_description.strip())
    if n < 50:
        raise ValueError(f"JD too short ({n} chars).")
    print(f"  [Tool] parse_job_description — {n} chars ✓")
    return {"status": "validated", "char_count": n}


@tool
def match_skills(profile: dict, requirements: dict) -> dict:
    """Validate inputs for skill matching analysis.

    Call this after parsing both the resume and job description.
    Pass the structured profile and requirements dicts.
    The agent will then produce a skill alignment analysis.

    Args:
        profile: Dict with resume data (name, skills, experience, etc).
        requirements: Dict with job data (title, required_skills, etc).
    """
    if not profile or not isinstance(profile, dict):
        raise ValueError("profile must be a non-empty dict")
    if not requirements or not isinstance(requirements, dict):
        raise ValueError("requirements must be a non-empty dict")
    print("  [Tool] match_skills — inputs validated ✓")
    return {
        "status": "validated",
        "profile": profile,
        "requirements": requirements,
    }


agent = Agent(
    model=model,
    tools=[parse_resume, parse_job_description, match_skills],
    system_prompt="""You are a resume optimization agent.

Workflow:
1. Parse resume text → produce structured JSON profile
2. Parse job description → produce structured JSON requirements
3. Call match_skills with both dicts
4. Produce a skill match analysis with:
   - matched_skills: skills the candidate has that the job requires
   - missing_skills: required skills the candidate lacks
   - transferable_skills: candidate skills mappable to requirements
   - keyword_coverage: float 0.0-1.0
   - recommendations: list of suggestions

Rules: matched_skills + missing_skills = all required_skills (no overlap)""",
)


RESUME = """
Maria Garcia
Email: maria.g@email.com

SUMMARY
ML engineer with 5 years building recommendation systems and NLP pipelines.

SKILLS
Python, TensorFlow, PyTorch, Spark, Kafka, AWS (SageMaker, Lambda, S3),
Docker, Kubernetes, SQL, Elasticsearch, scikit-learn, Airflow

EXPERIENCE
ML Engineer | RecSys Corp | 2021 - Present
- Built recommendation engine serving 20M users using collaborative filtering
- Deployed models on SageMaker with A/B testing framework
- Reduced inference latency by 40% through model optimization

Data Scientist | DataCo | 2019 - 2021
- Developed NLP pipeline for sentiment analysis (BERT fine-tuning)
- Built ETL pipelines with Spark processing 5TB daily

EDUCATION
M.S. Computer Science | Stanford | 2019
"""

JOB = """
Senior ML Engineer - Netflix
Required: Python, Deep Learning (TensorFlow or PyTorch), Recommendation Systems,
Distributed Computing, A/B Testing, SQL
Preferred: Spark, Kafka, Cloud platforms (AWS/GCP), NLP experience
Responsibilities: Design ML systems at scale, run experiments, mentor team
Qualifications: MS in CS/ML, 4+ years ML engineering
"""

if __name__ == "__main__":
    print("=== Skill Matching Demo ===\n")
    response = agent(
        f"Parse this resume and job description, then match skills.\n\n"
        f"Resume:\n{RESUME}\n\nJob Description:\n{JOB}"
    )
    print(response)

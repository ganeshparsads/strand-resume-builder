"""
Step 2: ATS-Friendly HTML Resume Generation
=============================================

This step adds the generate_resume_html tool. The agent takes
the parsed profile, skill match results, and job requirements,
then generates a complete HTML resume optimized for ATS systems.

ATS (Applicant Tracking System) rules for HTML:
- Use semantic tags: section, h1-h3, ul, li
- No JavaScript or external resources
- Clean structure that parsers can read
- Include all matched keywords from the job description

The tool validates inputs; the LLM generates the actual HTML.

Run: uv run python step2_html_generation.py
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
    return {"status": "validated", "char_count": n}


@tool
def match_skills(profile: dict, requirements: dict) -> dict:
    """Validate inputs for skill matching analysis.
    Args:
        profile: Dict with resume data.
        requirements: Dict with job data.
    """
    if not profile or not requirements:
        raise ValueError("Both profile and requirements required")
    return {"status": "validated", "profile": profile, "requirements": requirements}


@tool
def generate_resume_html(
    profile: dict,
    match_result: dict,
    job_requirements: dict,
    feedback: str = "",
    current_html: str = "",
) -> dict:
    """Validate inputs for ATS-friendly HTML resume generation.

    Call this after skill matching to generate a tailored HTML resume.
    The agent should produce complete HTML with:
    - Semantic tags (section, h1-h3, ul, li) for ATS compatibility
    - Inline CSS only (no external stylesheets)
    - No script tags or external resources
    - All matched_skills included in the output

    For refinement: provide feedback + current_html to modify existing resume.

    Args:
        profile: Dict with parsed resume data.
        match_result: Dict with skill matching results.
        job_requirements: Dict with parsed job requirements.
        feedback: Optional feedback for refinement.
        current_html: Optional existing HTML to refine.
    """
    if not profile:
        raise ValueError("profile required")
    if not match_result:
        raise ValueError("match_result required")
    if not job_requirements:
        raise ValueError("job_requirements required")
    if feedback and not current_html:
        raise ValueError("current_html required when feedback is provided")
    print("  [Tool] generate_resume_html — inputs validated ✓")
    return {"status": "validated"}


agent = Agent(
    model=model,
    tools=[parse_resume, parse_job_description, match_skills, generate_resume_html],
    system_prompt="""You are a professional resume optimization agent.

Workflow:
1. Parse resume → structured JSON
2. Parse job description → structured JSON
3. Match skills → alignment analysis
4. Call generate_resume_html with profile, match_result, job_requirements
5. Generate a COMPLETE ATS-friendly HTML resume

HTML rules:
- Use semantic tags: section, h1-h3, ul, li
- Inline CSS only (no external stylesheets or links)
- No script tags or external resources
- Include ALL matched_skills as keywords
- Professional, clean layout""",
)

RESUME = """
David Park
Email: david.park@email.com | Phone: (206) 555-0147

SUMMARY
Backend engineer specializing in distributed systems and cloud infrastructure.
6 years of experience building scalable services at high-traffic companies.

SKILLS
Go, Python, Java, gRPC, Kafka, Redis, PostgreSQL, DynamoDB,
AWS (ECS, Lambda, SQS, S3), Docker, Kubernetes, Terraform, CI/CD

EXPERIENCE
Senior Backend Engineer | StreamCo | 2022 - Present
- Designed event-driven architecture processing 100M events/day
- Built service mesh with Envoy reducing inter-service latency by 30%
- Led migration from monolith to microservices (12 services)

Backend Engineer | CloudBase | 2019 - 2022
- Developed real-time data pipeline with Kafka and Spark
- Implemented distributed caching layer reducing DB load by 60%
- Built automated deployment pipeline with Terraform and GitHub Actions

Software Engineer | TechStart | 2018 - 2019
- Created REST APIs serving 1M requests/day
- Implemented rate limiting and circuit breaker patterns

EDUCATION
B.S. Computer Science | University of Washington | 2018
"""

JOB = """
Staff Engineer, Platform Infrastructure - Stripe
Required: Distributed systems, Go or Java, Cloud infrastructure,
Service mesh, Event-driven architecture, Kubernetes
Preferred: Payment systems, gRPC, Terraform, Observability
Responsibilities: Design core platform services, define technical standards,
mentor engineers, drive reliability improvements
Qualifications: 6+ years backend engineering, distributed systems experience
"""

if __name__ == "__main__":
    print("=== HTML Resume Generation Demo ===\n")
    print("(This may take 60-90 seconds for the full pipeline)\n")
    response = agent(
        f"Parse resume and job description, match skills, then generate "
        f"a complete ATS-friendly HTML resume.\n\n"
        f"Resume:\n{RESUME}\n\nJob Description:\n{JOB}"
    )
    # Save the HTML output
    result = str(response)
    import re
    html_match = re.search(r"```html\s*([\s\S]*?)```", result)
    if html_match:
        with open("output_resume.html", "w") as f:
            f.write(html_match.group(1))
        print("\n✓ HTML resume saved to output_resume.html")
        print("  Open it in your browser to preview!")
    else:
        print(result[:2000])

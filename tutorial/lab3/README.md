# Lab 3: Skill Matching, HTML Generation & Version Management

## Objective
Add the remaining tools to complete the agent pipeline: skill matching, ATS-friendly HTML resume generation, and S3-backed version management. By the end, your agent handles the full resume optimization workflow.

## Prerequisites
- Completed Lab 2
- S3 bucket from Lab 2

## Step 1: Add Skill Matching Tool

This tool validates inputs for the agent's skill analysis:

```python
@tool
def match_skills(profile: dict, requirements: dict) -> dict:
    """Validate inputs for skill matching analysis.

    Args:
        profile: Dict conforming to ResumeProfile schema.
        requirements: Dict conforming to JobRequirements schema.
    """
    if not profile or not isinstance(profile, dict):
        raise ValueError("profile must be a non-empty dict")
    if not requirements or not isinstance(requirements, dict):
        raise ValueError("requirements must be a non-empty dict")
    return {
        "status": "validated",
        "profile": profile,
        "requirements": requirements,
    }
```

## Step 2: Add HTML Resume Generator Tool

```python
@tool
def generate_resume_html(
    profile: dict,
    match_result: dict,
    job_requirements: dict,
    feedback: str = "",
    current_html: str = "",
) -> dict:
    """Validate inputs for ATS-friendly HTML resume generation.

    Args:
        profile: Dict conforming to ResumeProfile schema.
        match_result: Dict conforming to SkillMatchResult schema.
        job_requirements: Dict conforming to JobRequirements schema.
        feedback: Optional refinement feedback.
        current_html: Optional current HTML to refine.
    """
    if not profile:
        raise ValueError("profile required")
    if not match_result:
        raise ValueError("match_result required")
    if not job_requirements:
        raise ValueError("job_requirements required")
    if feedback and not current_html:
        raise ValueError("current_html required when feedback provided")
    return {"status": "validated"}
```

## Step 3: Add Version Management Tool

This tool stores and retrieves resume versions in S3:

```python
import json
from datetime import datetime, timezone

@tool
def manage_versions(
    action: str,
    session_id: str,
    html_content: str = "",
    version_id: str = "",
    feedback: str = "",
) -> dict:
    """Manage resume version history in S3.

    Args:
        action: One of save, get_latest, get, list.
        session_id: Session UUID.
        html_content: HTML to save (required for save).
        version_id: Version to retrieve (required for get).
        feedback: Feedback that produced this version.
    """
    s3 = boto3.client("s3", region_name=AWS_REGION)
    prefix = f"versions/{session_id}/"

    if action == "save":
        if not html_content:
            raise ValueError("html_content required for save")
        vid = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        record = {
            "version_id": vid,
            "session_id": session_id,
            "timestamp": ts,
            "html_content": html_content,
            "feedback": feedback or None,
        }
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=f"{prefix}{vid}.json",
            Body=json.dumps(record),
        )
        return {"status": "saved", "record": record}

    elif action == "list":
        resp = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
        versions = []
        for obj in resp.get("Contents", []):
            data = s3.get_object(Bucket=S3_BUCKET, Key=obj["Key"])
            versions.append(json.loads(data["Body"].read()))
        versions.sort(key=lambda v: v["timestamp"], reverse=True)
        return {"status": "found", "count": len(versions), "versions": versions}

    elif action == "get_latest":
        resp = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
        versions_list = []
        for obj in resp.get("Contents", []):
            data = s3.get_object(Bucket=S3_BUCKET, Key=obj["Key"])
            versions_list.append(json.loads(data["Body"].read()))
        versions_list.sort(key=lambda v: v["timestamp"], reverse=True)
        if versions_list:
            return {"status": "found", "record": versions_list[0]}
        return {"status": "empty", "record": {}}

    elif action == "get":
        key = f"{prefix}{version_id}.json"
        try:
            data = s3.get_object(Bucket=S3_BUCKET, Key=key)
            return {"status": "found", "record": json.loads(data["Body"].read())}
        except Exception:
            raise ValueError(f"Version {version_id} not found")

    raise ValueError(f"Invalid action: {action}")
```

## Step 4: Update the Agent with All 6 Tools

```python
agent = Agent(
    model=model,
    tools=[
        extract_text_from_pdf,
        parse_resume,
        parse_job_description,
        match_skills,
        generate_resume_html,
        manage_versions,
    ],
    system_prompt="""You are a professional resume optimization agent.

Available tools:
- extract_text_from_pdf: Extract text from base64-encoded PDF
- parse_resume: Validate resume text for parsing
- parse_job_description: Validate job description text
- match_skills: Validate inputs for skill matching
- generate_resume_html: Validate inputs for HTML generation
- manage_versions: Save/retrieve resume versions in S3

Full workflow:
1. Extract text from PDF if provided
2. Parse resume text into structured JSON
3. Parse job description into structured JSON
4. Match skills between resume and job requirements
5. Generate ATS-friendly HTML resume with semantic tags (section, h1-h3, ul, li)
6. Save the version using manage_versions

No script tags or external resources in HTML output.
For refinement: get latest version, apply feedback, save new version.""",
)
```

## Step 5: Test the Full Pipeline

Create `test_full.py`:

```python
import base64
import uuid
from agent import agent

with open("resume.pdf", "rb") as f:
    pdf_b64 = base64.b64encode(f.read()).decode()

SESSION_ID = str(uuid.uuid4())

JOB_DESC = """
Senior ML Engineer - Amazon
Required: Python, Java, ML (TensorFlow, PyTorch), AWS (SageMaker, Lambda, S3),
Distributed systems, Docker, Kubernetes
Preferred: Recommendation systems, NLP, Spark, Kafka, CI/CD
Responsibilities: Design ML pipelines, collaborate with scientists,
optimize model inference, mentor engineers
Qualifications: MS CS, 5+ years ML engineering
"""

# Pre-extract PDF text to keep prompt small
from agent import extract_text_from_pdf as _extract
# Call the underlying function directly
resume_text = _do_extract_text_from_pdf(pdf_b64)

response = agent(
    f"Here is my resume text and a job description. "
    f"Parse both, match skills, generate an ATS-friendly HTML resume, "
    f"and save the version with session_id '{SESSION_ID}'.\n\n"
    f"Resume:\n{resume_text}\n\n"
    f"Job Description:\n{JOB_DESC}"
)
print(str(response)[:3000])
```

```bash
uv run python test_full.py
```

## What You Learned
- How to build a multi-tool agent pipeline
- How to store/retrieve data in S3 from tools
- How the agent chains 5+ tool calls in sequence
- How version management enables iterative refinement

## Next: Lab 4
In Lab 4, you'll deploy to AgentCore and add a web frontend.

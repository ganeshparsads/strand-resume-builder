# Lab 1: Basic Agent Setup with Strands SDK

## Objective
Build your first AI agent using the Strands Agents SDK and Amazon Bedrock. By the end of this lab, you'll have a working conversational agent that can parse resumes from plain text.

## Prerequisites
- Python 3.12+
- AWS account with Bedrock model access (Claude 3.7 Sonnet)
- AWS credentials configured (`aws configure` or `ada credentials update`)

## Step 1: Project Setup

Initialize a new Python project with `uv`:

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# Create project
uv init resume-agent --python 3.12
cd resume-agent
uv venv --python 3.12

# Install dependencies
uv add strands-agents boto3
```

## Step 2: Create Your First Agent

Create `agent.py`:

```python
import os
from strands import Agent
from strands.models.bedrock import BedrockModel

model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
)

agent = Agent(
    model=model,
    system_prompt="You are a helpful assistant that answers questions concisely.",
)

# Test it
response = agent("What is an ATS-friendly resume?")
print(response)
```

Run it:
```bash
uv run python agent.py
```

You should see the agent respond with an explanation of ATS-friendly resumes.

## Step 3: Add a Custom Tool

Tools let the agent perform actions. Create a `parse_resume` tool that validates resume text:

```python
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
        raise ValueError(f"Resume too short ({n} chars). Min 100.")
    if n > 50_000:
        raise ValueError(f"Resume too long ({n} chars). Max 50000.")
    return {"status": "validated", "char_count": n}


agent = Agent(
    model=model,
    tools=[parse_resume],
    system_prompt="""You are a resume parsing agent.
When given resume text, call parse_resume to validate it,
then extract structured JSON with: name, email, phone, summary,
skills, experience, education. Only extract what's in the text.""",
)
```

## Step 4: Test with Sample Resume

Add a test script `main.py`:

```python
from agent import agent

SAMPLE_RESUME = """
John Smith
Email: john.smith@email.com | Phone: (555) 123-4567

PROFESSIONAL SUMMARY
Experienced software engineer with 5+ years in Python and AWS.

SKILLS
Python, Java, AWS, Docker, Kubernetes, PostgreSQL, REST APIs

EXPERIENCE
Senior Software Engineer | Acme Corp | Jan 2021 - Present
- Led migration to microservices, reducing deploy time by 60%
- Built data pipeline processing 1M+ events/day

Software Engineer | StartupXYZ | Jun 2018 - Dec 2020
- Built recommendation engine for 10M+ users
- Optimized queries reducing p99 latency from 500ms to 50ms

EDUCATION
M.S. Computer Science | Stanford University | 2018
B.S. Computer Science | UC Berkeley | 2016
"""

print("Sending resume for parsing...\n")
response = agent(
    f"Parse this resume into structured JSON:\n\n{SAMPLE_RESUME}"
)
print(response)
```

Run:
```bash
uv run python main.py
```

## What You Learned
- How to create a Strands agent with a Bedrock model
- How to define custom tools with the `@tool` decorator
- How the agent decides when to call tools based on the prompt
- How to structure a system prompt for specific tasks

## Next: Lab 2
In Lab 2, you'll add PDF support using AWS Textract and a job description parser.

"""
Step 2: Your First Tool — Teaching the Agent to Do Things
==========================================================

Tools are Python functions that the agent can call. The agent's LLM
decides WHEN to call a tool based on the user's message and the tool's
description.

Key concepts:
- @tool decorator: Transforms a Python function into an agent tool
- The function's docstring becomes the tool description the LLM reads
- The function's type hints become the parameter schema
- The agent decides autonomously whether to call the tool

How it works:
1. You give the agent a message
2. The LLM reads the message + available tool descriptions
3. The LLM decides: "I should call parse_resume with this text"
4. Strands calls your Python function with the arguments
5. The function returns a result
6. The LLM uses the result to formulate its response

Run: uv run python step2_first_tool.py
"""

import os
from strands import Agent, tool
from strands.models.bedrock import BedrockModel

model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
)


# --- Step 2a: Define a tool ---
# The @tool decorator transforms this function into something the agent
# can call. The docstring and type hints are critical — the LLM reads
# them to understand what the tool does and what parameters it needs.
@tool
def parse_resume(resume_text: str) -> dict:
    """Validate resume text for structured parsing.

    Call this tool when the user provides resume text that needs
    to be parsed into a structured format.

    Args:
        resume_text: Plain text content of a resume (100-50000 chars).
    """
    # This function does the actual work — validation in this case.
    # The agent's LLM handles the intelligent extraction.
    text_length = len(resume_text.strip())

    if text_length < 100:
        raise ValueError(
            f"Resume too short ({text_length} chars). Minimum is 100."
        )
    if text_length > 50_000:
        raise ValueError(
            f"Resume too long ({text_length} chars). Maximum is 50,000."
        )

    print(f"  [Tool called] parse_resume — {text_length} chars validated ✓")

    return {
        "status": "validated",
        "char_count": text_length,
        "message": "Resume text is valid. Proceed with extraction.",
    }


# --- Step 2b: Create agent with the tool ---
# Pass tools as a list. The agent now knows about parse_resume
# and will call it when appropriate.
agent = Agent(
    model=model,
    tools=[parse_resume],
    system_prompt="""You are a resume parsing agent.

When given resume text:
1. Call parse_resume to validate the text
2. Then extract structured JSON with these fields:
   name, email, phone, summary, skills, experience, education
3. Only extract information present in the text — never fabricate

Return the structured data as JSON.""",
)


# --- Step 2c: Test with a short text (should fail validation) ---
print("=== Test 1: Short text (should fail) ===\n")
response = agent("Parse this resume: John Smith, Python developer")
print(f"\nResponse: {response}\n")


# --- Step 2d: Test with a proper resume ---
print("\n=== Test 2: Full resume (should succeed) ===\n")

SAMPLE_RESUME = """
Jane Doe
Email: jane.doe@email.com | Phone: (555) 987-6543

PROFESSIONAL SUMMARY
Full-stack engineer with 6 years of experience building web applications
and distributed systems. Expert in Python, React, and AWS.

SKILLS
Python, JavaScript, React, Node.js, AWS, Docker, PostgreSQL, Redis,
GraphQL, CI/CD, Terraform, Kubernetes

EXPERIENCE
Senior Engineer | TechCorp | Mar 2021 - Present
- Architected microservices platform serving 5M daily users
- Reduced API latency by 40% through caching and query optimization
- Led team of 4 engineers on payment processing system

Software Engineer | WebStartup | Jan 2018 - Feb 2021
- Built real-time analytics dashboard using React and D3.js
- Implemented OAuth2 authentication system
- Deployed applications on AWS ECS with Terraform

EDUCATION
B.S. Computer Science | MIT | 2017
"""

response = agent(f"Parse this resume into structured JSON:\n\n{SAMPLE_RESUME}")
print(f"\nResponse:\n{response}")

"""
Step 3: Multi-Turn Conversation — Agent Memory
================================================

The Strands agent maintains conversation history automatically.
Each call to agent("message") adds to the conversation, so the
agent remembers what was said before.

This is important for our resume app because users will:
1. First submit their resume
2. Then ask for refinements ("make it more concise", "add metrics")
3. The agent needs to remember the original resume

Key concepts:
- Conversation history is maintained automatically
- Each agent() call builds on previous context
- The agent can reference earlier messages in its responses

Run: uv run python step3_conversation.py
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
        raise ValueError(f"Resume too short ({n} chars). Min 100.")
    print(f"  [Tool called] parse_resume — {n} chars ✓")
    return {"status": "validated", "char_count": n}


agent = Agent(
    model=model,
    tools=[parse_resume],
    system_prompt="""You are a resume optimization agent.
Parse resumes into structured JSON when provided.
Remember previous context for follow-up requests.
Keep responses concise.""",
)

SAMPLE_RESUME = """
Alex Johnson
Email: alex.j@email.com | Phone: (555) 111-2222

SUMMARY
Backend engineer with 4 years of experience in Python and cloud services.

SKILLS
Python, Go, AWS, Docker, Kubernetes, PostgreSQL, Redis, gRPC, Terraform

EXPERIENCE
Software Engineer | CloudCo | Jun 2020 - Present
- Built event-driven microservices processing 2M events/day
- Reduced infrastructure costs by 35% through right-sizing
- Implemented CI/CD pipeline with GitHub Actions

Junior Developer | DevShop | Aug 2018 - May 2020
- Developed REST APIs using Django and PostgreSQL
- Wrote unit tests achieving 90% code coverage

EDUCATION
B.S. Computer Science | Georgia Tech | 2018
"""

# --- Turn 1: Parse the resume ---
print("=== Turn 1: Parse resume ===\n")
response = agent(f"Parse this resume:\n\n{SAMPLE_RESUME}")
print(f"Agent: {str(response)[:500]}\n")

# --- Turn 2: Ask a follow-up (agent remembers the resume) ---
print("\n=== Turn 2: Follow-up question ===\n")
response = agent("What are the top 3 skills from this resume for a DevOps role?")
print(f"Agent: {response}\n")

# --- Turn 3: Ask for a modification ---
print("\n=== Turn 3: Request modification ===\n")
response = agent(
    "Rewrite the professional summary to emphasize cloud infrastructure "
    "and DevOps experience. Keep it to 2 sentences."
)
print(f"Agent: {response}")

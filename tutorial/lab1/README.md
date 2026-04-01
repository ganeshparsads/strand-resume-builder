# Lab 1: Basic Agent Setup with Strands SDK

## Overview
Build your first AI agent using the Strands Agents SDK and Amazon Bedrock. You'll progress through 4 steps, each building on the last.

| Step | File | What You Learn |
|------|------|----------------|
| Setup | `setup.sh` | Project initialization with uv |
| 1 | `step1_hello_agent.py` | Create an agent, send a message, get a response |
| 2 | `step2_first_tool.py` | Define a `@tool`, see the agent call it autonomously |
| 3 | `step3_conversation.py` | Multi-turn conversation with memory |
| 4 | `step4_resume_agent.py` | Complete interactive resume parsing agent |

## Prerequisites
- Python 3.12+
- AWS account with Bedrock model access (Claude 3.7 Sonnet enabled)
- AWS credentials configured (`aws configure` or `ada credentials update`)

## Quick Start

```bash
cd tutorial/lab1
chmod +x setup.sh
./setup.sh
```

Then run each step in order:
```bash
uv run python step1_hello_agent.py
uv run python step2_first_tool.py
uv run python step3_conversation.py
uv run python step4_resume_agent.py
```

## Step-by-Step Guide

### Step 1: Hello Agent (`step1_hello_agent.py`)

The simplest possible agent. Three lines of setup:

```python
model = BedrockModel(model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0", ...)
agent = Agent(model=model, system_prompt="...")
response = agent("Your message here")
```

**Key takeaway:** `BedrockModel` configures the LLM, `Agent` wraps it, and calling `agent("message")` sends a request to Bedrock and returns the response.

### Step 2: First Tool (`step2_first_tool.py`)

Introduces the `@tool` decorator — the core of Strands' power:

```python
@tool
def parse_resume(resume_text: str) -> dict:
    """Validate resume text for structured parsing.
    Args:
        resume_text: Plain text content of a resume.
    """
    # Your logic here
    return {"status": "validated"}
```

The LLM reads the docstring and type hints to understand:
- What the tool does (from the docstring)
- What parameters it needs (from the Args)
- What it returns (from the return type)

The agent then decides autonomously when to call it.

**Key takeaway:** You define tools as regular Python functions. The `@tool` decorator + docstring is all the LLM needs to use them.

### Step 3: Conversation Memory (`step3_conversation.py`)

Shows that the agent remembers previous messages:
- Turn 1: Parse a resume
- Turn 2: Ask about the resume (agent remembers it)
- Turn 3: Request a modification (agent uses prior context)

**Key takeaway:** Conversation history is automatic. Each `agent()` call builds on the previous context.

### Step 4: Complete Resume Agent (`step4_resume_agent.py`)

Puts it all together into an interactive agent with:
- A detailed system prompt defining the extraction schema
- Input validation via the `parse_resume` tool
- A rich sample resume for demo
- An interactive loop for follow-up questions

**Key takeaway:** The system prompt is where you define the agent's behavior, output format, and rules. The tool handles validation while the LLM handles intelligent extraction.

## Key Concepts Summary

| Concept | What It Does |
|---------|-------------|
| `BedrockModel` | Configures which LLM to use (model ID + region) |
| `Agent` | Wraps the model, manages conversation, orchestrates tools |
| `@tool` | Transforms a Python function into an agent-callable tool |
| `system_prompt` | Sets the agent's personality, rules, and output format |
| `agent("message")` | Sends a message and returns the LLM's response |

## Common Issues

| Issue | Fix |
|-------|-----|
| `InvalidClientTokenId` | AWS credentials expired. Run `aws configure` or refresh with ada |
| `AccessDeniedException` on Bedrock | Enable Claude 3.7 Sonnet in the Bedrock console (Model Access) |
| `ModuleNotFoundError: strands` | Run `uv add strands-agents boto3` |

## Next: Lab 2
In Lab 2, you'll add PDF support using AWS Textract and a job description parser.

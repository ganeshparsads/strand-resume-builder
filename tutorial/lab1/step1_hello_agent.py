"""
Step 1: Hello Agent — Your First Strands Agent
================================================

This is the simplest possible Strands agent. It connects to Amazon Bedrock,
sends a message to Claude 3.7 Sonnet, and prints the response.

Key concepts:
- BedrockModel: Configures which LLM to use and in which AWS region
- Agent: The core class that wraps the model and handles conversations
- Calling agent("message") sends the message and returns the response

Run: uv run python step1_hello_agent.py
"""

import os
from strands import Agent
from strands.models.bedrock import BedrockModel

# --- Step 1a: Configure the model ---
# BedrockModel tells Strands which LLM to use.
# We're using Claude 3.7 Sonnet via Amazon Bedrock.
# The region must match where you have Bedrock model access enabled.
model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
)

# --- Step 1b: Create the agent ---
# The Agent wraps the model and adds conversation management.
# system_prompt sets the agent's personality and behavior.
agent = Agent(
    model=model,
    system_prompt="You are a helpful assistant. Keep responses concise.",
)

# --- Step 1c: Talk to the agent ---
# Calling agent("message") sends the message to the LLM and returns
# the response. The agent handles all the Bedrock API calls internally.
print("Sending message to agent...\n")
response = agent("What is an ATS-friendly resume? Explain in 2-3 sentences.")

print("--- Agent Response ---")
print(response)

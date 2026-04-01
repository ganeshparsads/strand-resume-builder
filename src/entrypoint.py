"""AgentCore deployment entrypoint for the Resume Modifier Agent.

Wraps the Strands agent in a BedrockAgentCoreApp for serverless deployment.
Run locally: uv run python src/entrypoint.py
Deploy: agentcore configure --entrypoint src/entrypoint.py && agentcore launch
"""

import uuid
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from src.agent import create_agent

app = BedrockAgentCoreApp()
agent = create_agent()


@app.entrypoint
def invoke(payload: dict) -> dict:
    """AgentCore entrypoint. Receives user requests and routes to agent.

    Expected payload:
    {
        "session_id": "optional-uuid",
        "message": "required user message",
        "resume_file_path": "optional local path to PDF"
    }
    """
    session_id = payload.get("session_id", str(uuid.uuid4()))
    message = payload.get("message", "")
    resume_file_path = payload.get("resume_file_path", "")

    if not message:
        return {
            "error": "message is required",
            "session_id": session_id,
        }

    # Build the full prompt with context
    prompt = message
    if resume_file_path:
        prompt = (
            f"The user's resume PDF is at: {resume_file_path}\n"
            f"Session ID: {session_id}\n\n{message}"
        )

    try:
        result = agent(prompt)
        return {
            "session_id": session_id,
            "response": str(result),
        }
    except Exception as e:
        return {
            "session_id": session_id,
            "error": str(e),
        }

"""AgentCore deployment entrypoint for the Resume Modifier Agent.

Uses lazy initialization to stay within the 30s cold start limit.
"""

import uuid
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

# Lazy agent — initialized on first invoke, not at import time
_agent = None


def _get_agent():
    global _agent
    if _agent is None:
        from src.agent import create_agent
        _agent = create_agent()
    return _agent


@app.entrypoint
def invoke(payload: dict) -> dict:
    """AgentCore entrypoint."""
    session_id = payload.get("session_id", str(uuid.uuid4()))
    message = payload.get("message", "")

    if not message:
        return {"error": "message is required", "session_id": session_id}

    prompt = message
    resume_file_path = payload.get("resume_file_path", "")
    if resume_file_path:
        prompt = (
            f"The user's resume PDF is at: {resume_file_path}\n"
            f"Session ID: {session_id}\n\n{message}"
        )

    try:
        agent = _get_agent()
        result = agent(prompt)
        return {"session_id": session_id, "response": str(result)}
    except Exception as e:
        return {"session_id": session_id, "error": str(e)}

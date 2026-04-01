#!/bin/bash
# Lab 4 Setup Script
# Installs AgentCore toolkit

set -e

echo "=== Lab 4: Deploy to AgentCore + Frontend ==="
echo ""

echo "Installing AgentCore dependencies..."
uv add bedrock-agentcore
uv add --dev bedrock-agentcore-starter-toolkit

echo ""
echo "✓ AgentCore toolkit installed"
echo ""
echo "Next steps:"
echo "  1. Copy entrypoint.py from this lab directory"
echo "  2. Run: uv run python entrypoint.py  (test locally)"
echo "  3. Run: uv run agentcore configure -e entrypoint.py"
echo "  4. Run: uv run agentcore deploy"

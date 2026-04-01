#!/bin/bash
# Lab 1 Setup Script
# Run this to initialize the project and install dependencies

set -e

echo "=== Lab 1: Basic Agent Setup with Strands SDK ==="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
fi
echo "✓ uv installed: $(uv --version)"

if ! aws sts get-caller-identity &> /dev/null; then
    echo "✗ AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi
echo "✓ AWS credentials configured"

# Initialize project
echo ""
echo "Initializing Python project..."
uv init --python 3.12 .
uv venv --python 3.12
uv add strands-agents boto3

echo ""
echo "✓ Project ready! Run: uv run python step1_hello_agent.py"

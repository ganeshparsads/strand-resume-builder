# Lab 4: Deploy to AgentCore + Web Frontend

## Overview
Deploy the complete agent to Amazon Bedrock AgentCore Runtime and build a web frontend.

| Step | File | What You Learn |
|------|------|----------------|
| Setup | `setup.sh` | Install AgentCore toolkit |
| 1 | `step1_entrypoint.py` | Self-contained AgentCore entrypoint with all 6 tools |
| 2 | `step2_frontend/` | Static HTML/CSS/JS frontend (upload, preview, refine) |
| 3 | `step3_serve.py` | Dev proxy server (avoids CORS, serves frontend) |

## Prerequisites
- Completed Labs 1-3
- S3 bucket and `RESUME_S3_BUCKET` env var set
- A `resume.pdf` file for testing

## Quick Start — Local

```bash
cd tutorial/lab4
chmod +x setup.sh
./setup.sh

# Terminal 1: Start the agent
uv run python step1_entrypoint.py

# Terminal 2: Start the frontend proxy
uv run python step3_serve.py

# Browser: http://localhost:3000
```

## Quick Start — Deploy to AgentCore

```bash
# Configure (accept defaults)
uv run agentcore configure -e step1_entrypoint.py

# Deploy
uv run agentcore deploy

# Test
uv run agentcore invoke '{"prompt": "Hello, what can you do?"}'
```

## Step-by-Step Guide

### Step 1: AgentCore Entrypoint (`step1_entrypoint.py`)

The entrypoint is a self-contained Python file with all 6 tools defined inline. This is required because:

- AgentCore has a 30-second cold start timeout
- Cross-module imports can be slow
- Everything in one file = fast startup

Key patterns:
- `BedrockAgentCoreApp()` creates the HTTP server wrapper
- `@app.entrypoint` marks the request handler
- `app.run()` starts the local dev server on port 8080
- `BotocoreConfig(read_timeout=300)` prevents Bedrock timeouts on long generations
- PDF base64 is pre-extracted before sending to the LLM (keeps prompts small)

### Step 2: Frontend (`step2_frontend/`)

Three files:
- `index.html`: Layout with upload, text input, preview, version sidebar
- `app.js`: File handling, API calls, response parsing, version tracking
- `styles.css`: Responsive grid layout

The frontend sends `POST /invocations` with `{"prompt": "..."}` and reads `{"result": "..."}` from the response. HTML is extracted from markdown code blocks in the agent's response.

### Step 3: Dev Proxy (`step3_serve.py`)

A simple Python HTTP server that:
1. Serves `step2_frontend/` as static files on port 3000
2. Proxies `POST /invocations` to the agent on port 8080

This avoids CORS issues (browser blocks `file://` → `localhost:8080`).

## AgentCore Deployment Guide

### Configure

```bash
uv run agentcore configure -e step1_entrypoint.py
```

| Prompt | Answer |
|--------|--------|
| Deployment type | 1 (Direct Code Deploy) |
| Python version | PYTHON_3_12 |
| Execution role | Enter (auto-create) |
| S3 bucket | Enter (auto-create) |
| OAuth | no |
| Headers | no |
| Memory | s (skip) |

### Deploy

```bash
uv run agentcore deploy
```

### Test

```bash
uv run agentcore invoke '{"prompt": "Hello, what tools do you have?"}'
```

### Monitor

```bash
uv run agentcore status
```

## Architecture

```
Browser (localhost:3000)
    │
    ├── GET / ──────────→ step3_serve.py → step2_frontend/index.html
    │
    └── POST /invocations → step3_serve.py → localhost:8080 → step1_entrypoint.py
                                                                    │
                                                                    ├── extract_text_from_pdf (S3 + Textract)
                                                                    ├── parse_resume (validation)
                                                                    ├── parse_job_description (validation)
                                                                    ├── match_skills (validation)
                                                                    ├── generate_resume_html (validation)
                                                                    └── manage_versions (S3 CRUD)
                                                                    │
                                                                    └── Bedrock Claude 3.7 Sonnet (LLM reasoning)
```

## What You Built

A complete AI-powered resume optimization app:
- Strands Agents SDK for agent orchestration
- Amazon Bedrock (Claude 3.7 Sonnet) for LLM reasoning
- AWS Textract for PDF text extraction
- S3 for version storage
- AgentCore Runtime for serverless deployment
- Static HTML/JS frontend with dev proxy

# Lab 4: Deploy to AgentCore + Web Frontend

## Objective
Deploy your agent to Amazon Bedrock AgentCore Runtime and build a web frontend. By the end, you'll have a production-ready resume optimization app.

## Prerequisites
- Completed Lab 3
- All 6 tools working locally
- Node.js 18+ (for AgentCore CLI)

## Step 1: Install AgentCore Toolkit

```bash
uv add bedrock-agentcore
uv add --dev bedrock-agentcore-starter-toolkit
```

## Step 2: Create the Entrypoint

AgentCore needs a self-contained `entrypoint.py` at the project root. Key rules:
- Import `BedrockAgentCoreApp` from `bedrock_agentcore`
- Define all tools inline (no cross-module imports at startup)
- Use `@app.entrypoint` decorator for the invoke function
- Add `if __name__ == "__main__": app.run()` for local testing

Create `entrypoint.py`:

```python
import base64
import json
import os
import time
import uuid
from datetime import datetime, timezone

import boto3
from bedrock_agentcore import BedrockAgentCoreApp
from botocore.config import Config as BotocoreConfig
from strands import Agent, tool
from strands.models.bedrock import BedrockModel

app = BedrockAgentCoreApp()

AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
S3_BUCKET = os.environ.get("RESUME_S3_BUCKET", "your-bucket-name")

model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region_name=AWS_REGION,
    boto_client_config=BotocoreConfig(read_timeout=300),
)

# ... paste all 6 @tool functions here (from Lab 3) ...
# ... paste agent creation here ...

@app.entrypoint
def invoke(payload):
    """Process user input and return a response."""
    user_message = payload.get("prompt", payload.get("message", ""))
    if not user_message:
        return {"error": "prompt or message is required"}
    try:
        result = agent(user_message)
        return {"result": str(result)}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    app.run()
```

### Important: Self-Contained Entrypoint
AgentCore has a 30-second initialization timeout. If your entrypoint imports heavy modules from other files, it may exceed this limit. Keep everything in one file for deployment.

## Step 3: Test Locally

```bash
uv run python entrypoint.py
```

In another terminal:
```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, what can you do?"}'
```

## Step 4: Configure AgentCore

```bash
uv run agentcore configure -e entrypoint.py
```

You'll be prompted for:
| Prompt | Recommended Answer |
|---|---|
| Deployment type | 1 (Direct Code Deploy) |
| Python version | PYTHON_3_12 |
| Execution role | Press Enter (auto-create) |
| S3 bucket | Press Enter (auto-create) |
| OAuth | no |
| Header allowlist | no |
| Memory | s (skip) |

## Step 5: Deploy

```bash
uv run agentcore deploy
```

This will:
1. Package your code + dependencies
2. Upload to S3
3. Create/update the AgentCore runtime
4. Set up CloudWatch logging

## Step 6: Test the Deployed Agent

```bash
uv run agentcore invoke '{"prompt": "Hello, what tools do you have?"}'
```

## Step 7: Build the Frontend

Create `frontend/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume Modifier Agent</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="app">
        <header>
            <h1>Resume Modifier Agent</h1>
            <p>Upload your PDF resume and a job description.</p>
        </header>
        <main>
            <div class="input-panel">
                <section>
                    <h2>1. Upload Resume (PDF)</h2>
                    <input type="file" id="resume-upload" accept=".pdf">
                    <div id="file-info" hidden></div>
                </section>
                <section>
                    <h2>2. Paste Job Description</h2>
                    <textarea id="job-description" rows="10"
                        placeholder="Paste job description here..."></textarea>
                </section>
                <button id="generate-btn" disabled>Generate Tailored Resume</button>
                <div id="status" hidden></div>
            </div>
            <div class="output-panel">
                <h2>Resume Preview</h2>
                <div id="preview">Your resume will appear here.</div>
            </div>
        </main>
    </div>
    <script src="app.js"></script>
</body>
</html>
```

Create `frontend/app.js`:

```javascript
const AGENT_ENDPOINT = "";
let sessionId = crypto.randomUUID();
let selectedFile = null;

const resumeUpload = document.getElementById("resume-upload");
const jobDescription = document.getElementById("job-description");
const generateBtn = document.getElementById("generate-btn");
const preview = document.getElementById("preview");
const status = document.getElementById("status");

resumeUpload.addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (file && file.type === "application/pdf") {
    selectedFile = file;
    document.getElementById("file-info").textContent = file.name;
    document.getElementById("file-info").hidden = false;
    updateBtn();
  }
});

jobDescription.addEventListener("input", updateBtn);

function updateBtn() {
  generateBtn.disabled = !(selectedFile && jobDescription.value.trim().length >= 50);
}

generateBtn.addEventListener("click", async () => {
  generateBtn.disabled = true;
  status.textContent = "Generating resume... This takes 3-5 minutes.";
  status.hidden = false;

  const pdfBase64 = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(",")[1]);
    reader.onerror = reject;
    reader.readAsDataURL(selectedFile);
  });

  try {
    const resp = await fetch(`${AGENT_ENDPOINT}/invocations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt:
          `Extract text from the PDF, parse resume and job description, ` +
          `match skills, generate ATS-friendly HTML resume, save version.\n\n` +
          `Job Description:\n${jobDescription.value.trim()}\n\n` +
          `Resume PDF base64:\n${pdfBase64}`,
      }),
    });
    const data = await resp.json();
    if (data.error) {
      status.textContent = `Error: ${data.error}`;
      return;
    }
    const text = data.result || "";
    const htmlMatch = text.match(/```html\s*([\s\S]*?)```/);
    preview.innerHTML = htmlMatch ? htmlMatch[1] : text;
    status.textContent = "Done!";
  } catch (err) {
    status.textContent = `Failed: ${err.message}`;
  } finally {
    generateBtn.disabled = false;
    updateBtn();
  }
});
```

## Step 8: Serve the Frontend Locally

Since the frontend runs on `file://` and the agent on `localhost:8080`, you need a proxy to avoid CORS issues. Create `serve.py`:

```python
import http.server
import json
import os
import urllib.request

AGENT_URL = "http://localhost:8080"
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
PORT = 3000

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_POST(self):
        if self.path == "/invocations":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len)
            req = urllib.request.Request(
                f"{AGENT_URL}/invocations",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=600) as resp:
                    data = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())

if __name__ == "__main__":
    with http.server.HTTPServer(("", PORT), Handler) as httpd:
        print(f"Frontend: http://localhost:{PORT}")
        httpd.serve_forever()
```

Run both:
```bash
# Terminal 1: Agent
uv run python entrypoint.py

# Terminal 2: Frontend proxy
uv run python serve.py
```

Open `http://localhost:3000` in your browser.

## Architecture Summary

```
Browser (localhost:3000)
    │
    ├── GET / → serve.py → frontend/index.html
    │
    └── POST /invocations → serve.py → localhost:8080 → entrypoint.py
                                                            │
                                                            ├── extract_text_from_pdf (Textract)
                                                            ├── parse_resume
                                                            ├── parse_job_description
                                                            ├── match_skills
                                                            ├── generate_resume_html
                                                            └── manage_versions (S3)
```

## What You Learned
- How to deploy a Strands agent to AgentCore Runtime
- The self-contained entrypoint pattern for AgentCore
- How to build a frontend that communicates with the agent
- How to proxy requests to avoid CORS issues
- The full end-to-end architecture of an AI agent application

## Congratulations!
You've built a complete AI-powered resume optimization app using:
- Strands Agents SDK for agent orchestration
- Amazon Bedrock (Claude 3.7 Sonnet) for LLM reasoning
- AWS Textract for PDF text extraction
- S3 for version storage
- AgentCore Runtime for serverless deployment
- Static HTML/JS frontend with a dev proxy

"""
Step 3: Dev Proxy Server
=========================

This simple HTTP server does two things:
1. Serves the frontend static files (index.html, app.js, styles.css)
2. Proxies POST /invocations to the agent at localhost:8080

Why do we need this?
- The frontend runs on file:// or localhost:3000
- The agent runs on localhost:8080
- Browsers block cross-origin requests (CORS)
- This proxy puts both on the same origin

Usage:
  Terminal 1: uv run python step1_entrypoint.py    (agent on :8080)
  Terminal 2: uv run python step3_serve.py          (frontend on :3000)
  Browser:    http://localhost:3000
"""

import http.server
import json
import os
import urllib.request

AGENT_URL = "http://localhost:8080"
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "step2_frontend")
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
                # 10 min timeout — the full pipeline takes 3-6 minutes
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
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


if __name__ == "__main__":
    with http.server.HTTPServer(("", PORT), Handler) as httpd:
        print(f"Frontend:  http://localhost:{PORT}")
        print(f"Proxying:  POST /invocations → {AGENT_URL}/invocations")
        print(f"Serving:   {FRONTEND_DIR}")
        print()
        print("Open http://localhost:3000 in your browser")
        httpd.serve_forever()

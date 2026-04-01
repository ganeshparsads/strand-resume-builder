"""Simple dev server that serves frontend and proxies API to AgentCore."""

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
                self.send_header("Access-Control-Allow-Origin", "*")
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
        print(f"Frontend: http://localhost:{PORT}")
        print(f"Proxying API to: {AGENT_URL}")
        httpd.serve_forever()

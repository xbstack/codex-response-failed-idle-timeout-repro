#!/usr/bin/env python3
import argparse
import json
import os
import socketserver
import subprocess
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path

FAILURE_MARKER = "XBSTACK_LOCAL_TERMINAL_FAILURE"

class ThreadingHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def make_handler(hold_open: bool, hold_seconds: float):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):
            return

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            if length:
                self.rfile.read(length)
            body = {
                "type": "response.failed",
                "response": {
                    "id": "resp_xbstack_local_repro",
                    "status": "failed",
                    "error": {"code": "server_error", "message": FAILURE_MARKER},
                },
            }
            payload = f"event: response.failed\ndata: {json.dumps(body)}\n\n".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive" if hold_open else "close")
            self.end_headers()
            self.wfile.write(payload)
            self.wfile.flush()
            if hold_open:
                time.sleep(hold_seconds)
            self.close_connection = True

    return Handler


def run_case(codex_path: str, hold_open: bool, idle_ms: int):
    with ThreadingHTTPServer(("127.0.0.1", 0), make_handler(hold_open, max(2.0, idle_ms / 1000 + 1.0))) as server:
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        with tempfile.TemporaryDirectory(prefix="xbstack-codex-home-") as home:
            cfg = Path(home) / "config.toml"
            cfg.write_text(
                f'''model = "gpt-6-astra"\nmodel_provider = "xbstack_local"\nmodel_reasoning_effort = "medium"\n\n[model_providers.xbstack_local]\nname = "XBSTACK Local SSE Fixture"\nbase_url = "http://127.0.0.1:{port}/v1"\nwire_api = "responses"\nrequires_openai_auth = false\nrequest_max_retries = 0\nstream_max_retries = 0\nstream_idle_timeout_ms = {idle_ms}\n''',
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["CODEX_HOME"] = home
            started = time.monotonic()
            proc = subprocess.run(
                [codex_path, "exec", "--json", "Return exactly OK"],
                input="",
                text=True,
                capture_output=True,
                env=env,
                timeout=10,
            )
            duration_ms = round((time.monotonic() - started) * 1000)
            combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
            user_visible_error = ""
            for line in (proc.stdout or "").splitlines():
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("type") == "error":
                    user_visible_error = str(event.get("message") or "")
                    break
            return {
                "case": "failed_then_open_socket" if hold_open else "failed_then_eof",
                "returncode": proc.returncode,
                "duration_ms": duration_ms,
                "original_error_preserved": FAILURE_MARKER in combined,
                "idle_timeout_reported": "idle timeout waiting for SSE" in combined,
                "user_visible_error": user_visible_error,
            }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex", default="/Applications/ChatGPT.app/Contents/Resources/codex")
    parser.add_argument("--idle-ms", type=int, default=800)
    parser.add_argument("--output", type=Path, default=Path("logs/result.json"))
    args = parser.parse_args()
    results = [
        run_case(args.codex, False, args.idle_ms),
        run_case(args.codex, True, args.idle_ms),
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

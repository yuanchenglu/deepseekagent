#!/usr/bin/env python3
"""
Lightweight OpenAI-compatible API server for MLX models.
More reliable than mlx_lm server for many models.
Usage:
    python scripts/api-server.py --model ~/mlx-models/Qwen3.5-35B-A3B-4bit --port 8085

NOTE: mlx_lm.generate() does NOT accept temperature/temp kwargs
in some versions — omit them to avoid TypeError.
"""

import argparse, json, os, time, sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from mlx_lm import load, generate

model = None
tokenizer = None
model_path = None


def load_model(mpath):
    global model, tokenizer, model_path
    model_path = mpath
    print(f"Loading model: {mpath}", flush=True)
    t0 = time.time()
    model, tokenizer = load(mpath)
    print(f"Done ({time.time()-t0:.1f}s)", flush=True)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/v1/models":
            self.send_json({"object": "list", "data": [{"id": "qwen", "object": "model"}]})
        elif p == "/health":
            self.send_json({"status": "ok", "model": model_path})
        else:
            self.send_error(404)

    def do_POST(self):
        p = urlparse(self.path).path
        if p == "/v1/chat/completions":
            self.handle_chat()
        else:
            self.send_error(404)

    def handle_chat(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return self.send_json({"error": "invalid JSON"}, 400)

        messages = data.get("messages", [])
        if not messages:
            return self.send_json({"error": "missing messages"}, 400)

        prompt = ""
        for m in messages:
            if m["role"] == "user":
                prompt = m["content"] if isinstance(m["content"], str) else str(m["content"])

        max_tokens = data.get("max_tokens", 2048)

        prompt_text = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=False, add_generation_prompt=True
        )

        t0 = time.time()
        # 🚨 Do NOT pass temp/temperature — mlx_lm generate() rejects them
        response = generate(model, tokenizer, prompt=prompt_text,
                            max_tokens=max_tokens)
        elapsed = time.time() - t0

        result = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "model": "qwen",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": response.strip()}, "finish_reason": "stop"}],
            "usage": {
                "prompt_tokens": len(tokenizer.encode(prompt_text)),
                "completion_tokens": len(tokenizer.encode(response)),
                "total_tokens": len(tokenizer.encode(prompt_text)) + len(tokenizer.encode(response))
            }
        }
        self.send_json(result)

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def send_error(self, code):
        self.send_json({"error": "Not Found"}, code)

    def log_message(self, fmt, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {args[0]} {args[1]} {args[2]}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Model path")
    parser.add_argument("--port", type=int, default=8085, help="Port (default 8085 to avoid conflicts)")
    args = parser.parse_args()
    load_model(args.model)
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Server: http://localhost:{args.port}/v1", flush=True)
    server.serve_forever()

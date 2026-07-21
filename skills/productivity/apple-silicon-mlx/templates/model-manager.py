#!/usr/bin/env python3
"""
Local LLM Management Panel — FastAPI-based web UI for starting/stopping/testing local MLX models.

Usage:
  python model-manager-v2.py

Then open http://localhost:8083 in a browser.

Features:
- Start/stop any local MLX model (Qwen3.5-35B-A3B-4bit, Qwen3.6-27B-4bit, Qwen3.6-27B-6bit)
- Configure context length
- Chat interface for quick testing
- Model status monitoring
- Auto-selection of available models from ~/mlx-models/

Requires: FastAPI, uvicorn, httpx
  pip install fastapi uvicorn httpx
"""

import os, subprocess, time, atexit
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# ── CONFIG ──────────────────────────────
MODEL_DIR = os.path.expanduser("~/mlx-models")
MLX_PORT = 8085       # DFlash/MLX API port
MANAGE_PORT = 8083    # This management UI port
HOST = "0.0.0.0"

AVAILABLE_MODELS = {
    "Qwen3.5-35B-A3B-4bit": {
        "path": os.path.join(MODEL_DIR, "Qwen3.5-35B-A3B-4bit"),
        "desc": "MoE 35B (3.5B active), fastest, vision-capable"
    },
    "Qwen3.6-27B-4bit": {
        "path": os.path.join(MODEL_DIR, "Qwen3.6-27B-4bit"),
        "desc": "Dense 27B 4-bit, best coding quality"
    },
    "Qwen3.6-27B-6bit": {
        "path": os.path.join(MODEL_DIR, "Qwen3.6-27B-6bit"),
        "desc": "Dense 27B 6-bit, highest precision, memory hungry"
    },
}

app = FastAPI(title="Local LLM Manager")
mlx_process = None
current_model = None

def _port_used(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def _running():
    global mlx_process
    if mlx_process is None:
        return False
    if mlx_process.poll() is not None:
        mlx_process = None
        return False
    return True

class StartReq(BaseModel):
    model: str = "Qwen3.5-35B-A3B-4bit"
    context_length: int = 8192

@app.get("/api/status")
def status():
    r = _running()
    return {
        "running": r, "port_in_use": _port_used(MLX_PORT),
        "current_model": current_model if r else None,
        "port": MLX_PORT,
        "available_models": {k: {**v, "active": k == current_model and r}
                            for k, v in AVAILABLE_MODELS.items()},
        "api_url": f"http://127.0.0.1:{MLX_PORT}/v1" if r else None,
    }

@app.post("/api/start")
def start(req: StartReq):
    global mlx_process, current_model
    if req.model not in AVAILABLE_MODELS:
        raise HTTPException(400, f"Unknown model: {req.model}")
    if _running():
        raise HTTPException(400, "Model already running")
    os.system("pkill -f 'mlx_lm.server' 2>/dev/null; sleep 2")
    try:
        env = os.environ.copy()
        env["PATH"] = f"/opt/miniconda3/bin:{env.get('PATH', '')}"
        mlx_process = subprocess.Popen(
            ["mlx_lm.server", "--model", AVAILABLE_MODELS[req.model]["path"],
             "--port", str(MLX_PORT), "--host", "0.0.0.0", "--log-level", "INFO"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        current_model = req.model
        for _ in range(60):
            time.sleep(2)
            if _port_used(MLX_PORT):
                return {"success": True, "message": f"{req.model} started on :{MLX_PORT}"}
            if mlx_process.poll() is not None:
                out = mlx_process.stdout.read().decode()[:500] if mlx_process.stdout else ""
                mlx_process = None
                raise HTTPException(500, f"Start failed:\n{out}")
        raise HTTPException(500, "Timeout waiting for model")
    except Exception as e:
        mlx_process = None
        raise HTTPException(500, str(e))

@app.post("/api/stop")
def stop():
    global mlx_process
    os.system("pkill -f 'mlx_lm.server' 2>/dev/null")
    mlx_process = None
    return {"success": True}

# ── Frontend ──
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Local LLM Manager</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f0f13;color:#e0e0e0}
.container{max-width:900px;margin:0 auto;padding:20px}
header{display:flex;align-items:center;gap:12px;padding:16px 0;border-bottom:1px solid #2a2a3a;margin-bottom:20px}
.dot{width:10px;height:10px;border-radius:50%;display:inline-block}
.dot.on{background:#34d399;box-shadow:0 0 8px #34d39966}
.dot.off{background:#6b7280}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-bottom:16px}
.card{background:#1a1a24;border:1px solid #2a2a3a;border-radius:8px;padding:14px;cursor:pointer;transition:.2s}
.card:hover{border-color:#6366f1}
.card.active{border-color:#6366f1;background:#1e1e2e}
.card h3{font-size:14px;margin-bottom:4px}
.card p{font-size:12px;color:#888}
.ctrl{display:flex;gap:12px;margin-bottom:16px;align-items:center}
.btn{padding:8px 20px;border:none;border-radius:6px;font-size:14px;cursor:pointer;font-weight:500}
.btn-start{background:#34d399;color:#000}
.btn-start:disabled{background:#374151;color:#6b7280;cursor:not-allowed}
.btn-stop{background:#ef4444;color:#fff}
.btn-stop:disabled{background:#374151;color:#6b7280;cursor:not-allowed}
.info{background:#1a1a24;border:1px solid #2a2a3a;border-radius:8px;padding:12px 16px;margin-bottom:20px;font-size:13px}
#chatBox{background:#1a1a24;border:1px solid #2a2a3a;border-radius:8px;height:300px;overflow-y:auto;padding:16px;margin-bottom:12px;font-size:14px;line-height:1.6}
.msg{margin-bottom:10px}
.msg-u{color:#818cf8}.msg-u::before{content:'🧑 '}
.msg-a{color:#e0e0e0}.msg-a::before{content:'🤖 '}
.msg-s{color:#888;font-size:12px;text-align:center}
.row{display:flex;gap:8px}
.row textarea{flex:1;background:#1a1a24;border:1px solid #2a2a3a;border-radius:6px;padding:10px;color:#e0e0e0;font-size:14px;resize:none;height:44px}
.row textarea:focus{outline:none;border-color:#6366f1}
.row button{background:#6366f1;color:#fff;border:none;border-radius:6px;padding:0 20px;cursor:pointer}
.row button:disabled{background:#374151;cursor:not-allowed}
.hint{text-align:center;color:#6b7280;font-size:13px;padding:40px 0}
</style></head>
<body>
<div class="container">
<header><h1><span id="dot" class="dot off"></span> Local LLM Manager</h1><span id="st" style="font-size:13px;color:#888">checking...</span></header>
<div class="grid" id="grid"></div>
<div class="ctrl">
<button class="btn btn-start" id="btnS" onclick="start()">▶ Start</button>
<button class="btn btn-stop" id="btnT" onclick="stop()" disabled>■ Stop</button>
<div class="info" style="flex:1;margin:0"><span id="info">Select model then start</span></div>
</div>
<h2 style="font-size:16px;margin-bottom:8px">💬 Chat Test</h2>
<div id="chatBox"><div class="hint">Start model to chat</div></div>
<div class="row">
<textarea id="inp" placeholder="Type a message..." disabled></textarea>
<button id="btnSend" onclick="send()" disabled>Send</button></div></div>
<script>
let run=false,mod="",msgs=[];
async function api(u,o){const r=await fetch(u,{...o,headers:{'Content-Type':'application/json',...o.headers}});if(!r.ok)throw new Error((await r.text()).slice(0,200));return r.json()}
async function refresh(){try{
const d=await api('/api/status');run=d.running;
document.getElementById('dot').className='dot '+(run?'on':'off');
document.getElementById('st').textContent=run?'🟢 '+d.current_model:'⚪ stopped';
document.getElementById('btnS').disabled=run;document.getElementById('btnT').disabled=!run;
document.getElementById('inp').disabled=!run;document.getElementById('btnSend').disabled=!run;
document.getElementById('info').textContent=run?'🟢 '+d.current_model+' — API: '+d.api_url:'⚪ stopped';
const g=document.getElementById('grid');g.innerHTML='';
for(const[k,v]of Object.entries(d.available_models||{})){const c=document.createElement('div');
c.className='card'+(v.active?' active':'');c.innerHTML='<h3>'+k+'</h3><p>'+v.desc+'</p>';
c.onclick=()=>{if(!run){mod=k;refresh()}};g.appendChild(c);if(v.active)mod=k}
}catch(e){}}
async function start(){document.getElementById('btnS').disabled=true;document.getElementById('btnS').textContent='Starting...';
try{const d=await api('/api/start',{method:'POST',body:JSON.stringify({model:mod})});chat('✅ '+d.message)
}catch(e){chat('❌ '+e.message)}document.getElementById('btnS').textContent='▶ Start';await refresh()}
async function stop(){await api('/api/stop',{method:'POST'});chat('⏹ Stopped');await refresh();msgs=[]}
function chat(t,c){const b=document.getElementById('chatBox'),d=document.createElement('div');
d.className='msg msg-'+(c||'s');d.innerHTML=t;b.appendChild(d);b.scrollTop=b.scrollHeight}
async function send(){const i=document.getElementById('inp'),t=i.value.trim();if(!t)return;
i.value='';chat(t,'u');msgs.push({role:'user',content:t});
document.getElementById('btnSend').disabled=true;
const ld=document.createElement('div');ld.className='msg msg-s';ld.textContent='⏳ generating...';
document.getElementById('chatBox').appendChild(ld);
try{const d=await api('/api/chat',{method:'POST',body:JSON.stringify({messages:[...msgs],max_tokens:512})});
ld.remove();const r=d.choices?.[0]?.message?.content||'(empty)';chat(r,'a');msgs.push({role:'assistant',content:r})
}catch(e){ld.remove();chat('❌ '+e.message)}
document.getElementById('btnSend').disabled=false}
document.getElementById('inp').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});
refresh();setInterval(refresh,5000);
</script></body></html>"""

@app.get("/", response_class=HTMLResponse)
def index(): return HTML_PAGE

class ChatReq(BaseModel):
    messages: list
    temperature: float = 0.1
    max_tokens: int = 512

@app.post("/api/chat")
async def proxy_chat(req: ChatReq):
    if not _port_used(MLX_PORT):
        raise HTTPException(400, "Model not running")
    import httpx
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(f"http://127.0.0.1:{MLX_PORT}/v1/chat/completions", json={
            "model": current_model, "messages": req.messages,
            "temperature": req.temperature, "max_tokens": req.max_tokens})
        if r.status_code != 200:
            raise HTTPException(502, r.text[:200])
        return r.json()

if __name__ == "__main__":
    print(f"Management UI: http://127.0.0.1:{MANAGE_PORT}")
    uvicorn.run(app, host=HOST, port=MANAGE_PORT, log_level="warning")

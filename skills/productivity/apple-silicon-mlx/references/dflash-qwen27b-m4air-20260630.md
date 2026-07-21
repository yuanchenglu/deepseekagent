# Empirical Run: Qwen3.6-27B-4bit + DFlash on M4 Air 32GB

Date: 2026-06-30  
Hardware: MacBook Air M4, 32GB unified memory (120 GB/s bandwidth)  
Model: mlx-community/Qwen3.6-27B-4bit (target) + z-lab/Qwen3.6-27B-DFlash (draft)  
Framework: dflash-mlx v0.1.10 + mlx 0.31.2  
Download source: modelscope.cn (primary) + manual HF cache construction

## Download & Cache Setup (China network)

Used modelscope for speed (24–40 MB/s vs hf-mirror ~slow).

```python
from modelscope.hub.snapshot_download import snapshot_download
model_dir = snapshot_download('mlx-community/Qwen3.6-27B-4bit', cache_dir='/tmp/msc_main')
# Same for draft
```

Then manual conversion to HF hub format (hash + symlinks in blobs/ + snapshots/main/):

- Draft: 3.2 GB
- Target: 15.0 GB
- Total cache construction: reliable once hashes computed correctly.

## Server Startup

```bash
cd ~/dflash-mlx
dflash serve \
  --model mlx-community/Qwen3.6-27B-4bit \
  --draft z-lab/Qwen3.6-27B-DFlash \
  --port 8000
```

Pre-flight: `dflash doctor` (passed, with expected "NAX unavailable on M4" warning).

## Measured Performance (from server [dflash] logs)

| Req | Prompt tok | Gen tok | Decode tok/s | Acceptance | Notes |
|-----|------------|---------|--------------|------------|-------|
| 1   | 26         | 150     | 14.3         | 79.3%     | Short |
| 2   | 26         | 150     | 15.0         | 79.3%     | Short |
| 3   | 20         | 80      | 16.1         | 86.2%     | Best short |
| 4   | 31         | 400     | 10.7         | 64.5%     | Longer gen |

Prefill logical: 14–22 tok/s.

Client curl times were sometimes slower due to large reasoning_content output.

**Important**: Always read the server's stdout for `[dflash] decode X tok/s | Y% accepted`.

## API Response Structure Note

Model frequently emits to `reasoning_content`:
```json
"message": {
  "role": "assistant",
  "reasoning_content": "Here's a thinking process:\n...",
  "content": ""   // often empty or partial
}
```

Clients must extract from either field.

## Issues Encountered & Fixes

- Generation requests hung (HTTP 000 after 25–40s) after heavy use → kill and restart server.
- First requests after restart had lower speed until warm.
- Background `hf download` with HF_ENDPOINT was too slow → switched to modelscope.
- `--include` glob ignored by `hf download` → explicit filenames required.

## Memory Footprint (observed)

- mlx_active: 16.28–16.94 GB
- Process RSS peak: ~8.65 GB
- System remained responsive with other light apps closed.

## References / Logs

See full server output in the session for exact `[dflash]` lines and prefix-cache stats.

This run validated the conservative estimates in the main skill while showing slightly better short-context numbers (14–16 vs predicted ~10–14) under clean conditions.

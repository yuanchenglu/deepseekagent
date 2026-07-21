#!/usr/bin/env python3
"""
Download HuggingFace MLX models with retry support for unstable connections.
Usage:
    HF_ENDPOINT=https://hf-mirror.com python scripts/download-model.py \
        mlx-community/Qwen3.5-35B-A3B-4bit \
        ~/mlx-models/Qwen3.5-35B-A3B-4bit \
        --retries 10
"""

import argparse, os, sys, time
from pathlib import Path
from huggingface_hub import snapshot_download, HfHubHTTPError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_id", help="HF repo ID")
    parser.add_argument("local_dir", help="Local output dir")
    parser.add_argument("--retries", type=int, default=5, help="Max retries")
    parser.add_argument("--endpoint", help="HF endpoint override (sets HF_ENDPOINT)")
    args = parser.parse_args()

    if args.endpoint:
        os.environ.setdefault("HF_ENDPOINT", args.endpoint)

    local_dir = os.path.expanduser(args.local_dir)
    os.makedirs(local_dir, exist_ok=True)

    existing = list(Path(local_dir).glob("*.safetensors"))
    if existing:
        total = sum(f.stat().st_size for f in existing)
        print(f"Found {len(existing)} existing files ({total/1e9:.1f} GB)")

    for attempt in range(args.retries):
        try:
            t0 = time.time()
            snapshot_download(
                repo_id=args.repo_id,
                local_dir=local_dir,
                local_dir_use_symlinks=False,
                resume_download=True,
                max_workers=4,
            )
            total = sum(f.stat().st_size for f in Path(local_dir).glob("*.safetensors"))
            elapsed = time.time() - t0
            print(f"Done: {total/1e9:.1f} GB in {elapsed:.0f}s ({total/1e9/elapsed*60:.1f} GB/min)")
            return
        except (HfHubHTTPError, ConnectionError, TimeoutError, OSError) as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < args.retries - 1:
                time.sleep(5 * (attempt + 1))
    print("All retries exhausted")
    sys.exit(1)


if __name__ == "__main__":
    main()

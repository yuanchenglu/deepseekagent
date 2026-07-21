#!/usr/bin/env python3
"""
Download individual safetensor files one-at-a-time with retries.
More reliable than hf download for unstable networks (China, etc.)
where large files (>5GB) frequently time out.

Usage:
    python scripts/download-files.py <repo_id> <local_dir> [--retries 20]

Example:
    python scripts/download-files.py \\
        mlx-community/Qwen3.6-27B-4bit \\
        ~/mlx-models/Qwen3.6-27B-4bit \\
        --retries 20 --timeout 600
"""

import argparse, json, os, subprocess, sys, time
from pathlib import Path


def download_file(repo_id, filename, local_dir, endpoint, retries=15, timeout=300):
    """Download a single file, retrying on failure."""
    local_path = os.path.join(local_dir, filename)

    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        size = os.path.getsize(local_path)
        print(f"  [skip] {filename} ({size/1e9:.1f}GB)")
        return True

    for attempt in range(retries):
        print(f"  [{attempt+1}/{retries}] {filename}...", end=" ", flush=True)

        result = subprocess.run(
            ["hf", "download", repo_id, "--local-dir", local_dir, filename],
            capture_output=True, text=True,
            timeout=timeout,
            env={**os.environ, "HF_ENDPOINT": endpoint,
                 "HF_HUB_DOWNLOAD_TIMEOUT": str(timeout)}
        )

        if result.returncode == 0:
            size = os.path.getsize(local_path) if os.path.exists(local_path) else 0
            print(f"OK ({size/1e9:.1f}GB)")
            return True
        else:
            err = result.stderr.strip()[-120:] if result.stderr else "unknown error"
            print(f"FAILED: {err}")
            if attempt < retries - 1:
                wait = 10 * (attempt + 1)
                print(f"       retry in {wait}s...")
                time.sleep(wait)

    print(f"  GIVING UP on {filename}")
    return False


def main():
    parser = argparse.ArgumentParser(description="Download MLX model files individually")
    parser.add_argument("repo_id")
    parser.add_argument("local_dir")
    parser.add_argument("--endpoint", default="https://hf-mirror.com")
    parser.add_argument("--retries", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    local_dir = os.path.expanduser(args.local_dir)
    os.makedirs(local_dir, exist_ok=True)

    print(f"Fetching {args.repo_id} file list...")

    # Read index.json to determine required shards
    # First ensure config files are present
    download_file(args.repo_id, "model.safetensors.index.json", local_dir,
                  args.endpoint, retries=5, timeout=60)

    index_path = os.path.join(local_dir, "model.safetensors.index.json")
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)
        shards = sorted(set(index["weight_map"].values()))
        total = index.get("metadata", {}).get("total_size", 0)
        print(f"Need {len(shards)} shards, {total/1e9:.0f}GB total")

        ok = all(download_file(args.repo_id, shard, local_dir,
                               args.endpoint, args.retries, args.timeout)
                 for shard in shards)
        if not ok:
            print("Some files failed — check network and retry.")
            sys.exit(1)
    else:
        print("No index.json found; downloading all safetensors...")
        # Fallback: list remote files
        result = subprocess.run(
            ["hf", "ls", args.repo_id],
            capture_output=True, text=True,
            env={**os.environ, "HF_ENDPOINT": args.endpoint}
        )
        for line in result.stdout.splitlines():
            if line.endswith(".safetensors"):
                download_file(args.repo_id, line, local_dir,
                              args.endpoint, args.retries, args.timeout)

    total_size = sum(f.stat().st_size for f in Path(local_dir).glob("*.safetensors"))
    print(f"\nDone: {total_size/1e9:.1f} GB downloaded to {local_dir}")


if __name__ == "__main__":
    main()

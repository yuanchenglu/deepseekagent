#!/usr/bin/env python3
"""Batch translate all remaining papers in papers/ directory."""
import os, sys, time

# Read API key from env file (more reliable than source in background)
env_file = os.path.expanduser("~/.hermes/.env")
with open(env_file) as f:
    for line in f:
        if line.startswith("DEEPSEEK_API_KEY="):
            os.environ["DEEPSEEK_API_KEY"] = line.strip().split("=", 1)[1]
            break

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from translate import translate_file

PAPERS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "papers")

# List all papers that have .txt but no _zh.txt
TODO = []
for f in sorted(os.listdir(PAPERS_DIR)):
    if f.endswith('.txt') and '_zh' not in f:
        paper_id = f.replace('.txt', '')
        zh_path = os.path.join(PAPERS_DIR, f"{paper_id}_zh.txt")
        if not os.path.exists(zh_path) or os.path.getsize(zh_path) < 1000:
            TODO.append(paper_id)

print(f"Papers to translate: {len(TODO)}")
for pid in TODO:
    print(f"  - {pid}")

success, failed = 0, 0
for paper_id in TODO:
    input_path = os.path.join(PAPERS_DIR, f"{paper_id}.txt")
    output_path = os.path.join(PAPERS_DIR, f"{paper_id}_zh.txt")
    
    if not os.path.exists(input_path):
        print(f"SKIP {paper_id} (source missing)")
        continue
    
    print(f"\n>>> [{success+failed+1}/{len(TODO)}] Translating {paper_id}...")
    try:
        translate_file(input_path, output_path)
        success += 1
        print(f"DONE {paper_id}: {os.path.getsize(output_path):,} bytes")
    except Exception as e:
        failed += 1
        print(f"FAILED {paper_id}: {e}")
    
    time.sleep(2)  # avoid rate limiting

print(f"\n{'='*40}")
print(f"COMPLETE: {success} success, {failed} failed, {len(TODO)} total")

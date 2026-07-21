#!/usr/bin/env python3
"""Translate a single academic paper using DeepSeek API."""
import os, sys, time, json, urllib.request, urllib.error

# Force unbuffered output (for background process visibility)
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_BASE = "https://api.deepseek.com/v1"
MODEL = "deepseek-chat"

CHUNK_SIZE = 3000
MAX_RETRIES = 3


def call_api(messages, max_tokens=4000):
    url = f"{API_BASE}/chat/completions"
    data = json.dumps({
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.3
    }).encode()
    
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, data=data, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            })
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  API error (attempt {attempt+1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(3 * (attempt + 1))
    return None


def translate_chunk(text, chunk_num, total_chunks):
    sys_msg = """You are a professional academic translator. Translate the following English academic paper content to Simplified Chinese.

Rules:
1. Preserve ALL LaTeX formulas, equations, and math expressions as-is
2. Preserve ALL code blocks as-is
3. Preserve ALL table structures
4. Preserve ALL citation markers like [1], [2,3], etc.
5. Use professional academic Chinese style
6. Translate ALL content, do not summarize or skip
7. Keep section headers translated but preserve their numbering"""
    
    prompt = f"Translate this chunk ({chunk_num}/{total_chunks}) to Simplified Chinese:\n\n{text}"
    
    return call_api([
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": prompt}
    ])


def split_into_chunks(text, chunk_size=CHUNK_SIZE):
    paragraphs = text.split('\n\n')
    chunks = []
    current = ""
    
    for para in paragraphs:
        if len(current) + len(para) < chunk_size:
            current += para + '\n\n'
        else:
            if current:
                chunks.append(current.strip())
            current = para + '\n\n'
    if current:
        chunks.append(current.strip())
    
    return chunks


def translate_file(input_path, output_path):
    print(f"\n{'='*60}")
    print(f"Translating: {os.path.basename(input_path)}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"  Total chars: {len(text):,}")
    
    chunks = split_into_chunks(text, CHUNK_SIZE)
    total = len(chunks)
    print(f"  Split into {total} chunks of ~{CHUNK_SIZE} chars each")
    
    translated_chunks = []
    for i, chunk in enumerate(chunks, 1):
        print(f"  [{i}/{total}] Translating chunk ({len(chunk)} chars)...", end=' ', flush=True)
        start = time.time()
        result = translate_chunk(chunk, i, total)
        elapsed = time.time() - start
        
        if result:
            translated_chunks.append(result)
            print(f"OK ({elapsed:.1f}s)")
        else:
            print(f"FAILED after {MAX_RETRIES} retries")
            translated_chunks.append(f"[TRANSLATION FAILED]\n{chunk}")
        
        time.sleep(0.5)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(translated_chunks))
    
    output_size = os.path.getsize(output_path)
    print(f"  Saved: {output_path} ({output_size:,} bytes)")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: translate.py <arxiv_id>")
        sys.exit(1)
    
    arxiv_id = sys.argv[1]
    base = os.path.dirname(os.path.abspath(__file__))
    input_path = f"{base}/papers/{arxiv_id}.txt"
    output_path = f"{base}/papers/{arxiv_id}_zh.txt"
    
    if not os.path.exists(input_path):
        print(f"ERROR: {input_path} not found")
        sys.exit(1)
    
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        print(f"SKIP: {output_path} already exists")
        sys.exit(0)
    
    translate_file(input_path, output_path)

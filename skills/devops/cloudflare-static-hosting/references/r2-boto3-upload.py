#!/usr/bin/env python3
"""
Upload files to a Cloudflare R2 bucket using boto3 (S3-compatible API).

Usage:
  python3 r2-boto3-upload.py <bucket-name> <directory> [file1 file2 ...]

If no files specified, uploads default resume site files.
Requires env vars: R2_ACCESS_KEY, R2_SECRET_KEY, R2_ACCOUNT_ID
"""
import boto3, os, sys
from pathlib import Path

ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID", "")
ACCESS_KEY = os.environ.get("R2_ACCESS_KEY", "")
SECRET_KEY=os.env...Y", "")
ENDPOINT = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"
CT = {".html":"text/html; charset=utf-8",".md":"text/markdown; charset=utf-8",".pdf":"application/pdf",
      ".json":"application/json",".css":"text/css",".js":"application/javascript",
      ".png":"image/png",".jpg":"image/jpeg",".svg":"image/svg+xml",".ico":"image/x-icon"}
DF = ["index.html","resume.md","resume.en.md","resume.pdf","resume.en.pdf"]

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <bucket> <directory> [files...]"); sys.exit(1)
    bucket, directory = sys.argv[1], Path(sys.argv[2])
    files = sys.argv[3:] if len(sys.argv) > 3 else DF
    if not ACCESS_KEY or not SECRET_KEY:
        print("ERROR: Set R2_ACCESS_KEY and R2_SECRET_KEY env vars"); sys.exit(1)
    client = boto3.client("s3", endpoint_url=ENDPOINT, aws_access_key_id=ACCESS_KEY,
                          aws_secret_access_key=SECRET_KEY, region_name="auto")
    for fname in files:
        fp = directory / fname
        if not fp.exists(): print(f"  ⚠  {fname} not found"); continue
        ext = fp.suffix.lower()
        with open(fp,"rb") as f:
            client.put_object(Bucket=bucket, Key=fname, Body=f, ContentType=CT.get(ext,"application/octet-stream"))
        print(f"  ✅ {fname:25s} ({fp.stat().st_size/1024:.0f} KB)")

if __name__ == "__main__": main()

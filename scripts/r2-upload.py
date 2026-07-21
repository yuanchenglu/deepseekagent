#!/usr/bin/env python3
"""Upload a file to Cloudflare R2 using S3-compatible API (std lib only)."""
import hashlib, hmac, os, sys, time, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path

ENDPOINT = "https://d0a9c688290c80b51d6d4605ba32160a.r2.cloudflarestorage.com"
BUCKET = "deepagent-releases"
REGION = "auto"

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def hmac_sha256(key: bytes, msg: bytes) -> bytes:
    return hmac.new(key, msg, hashlib.sha256).digest()

def get_signature_key(key: str, date_stamp: str, region: str, service: str) -> bytes:
    k_date = hmac_sha256(f"AWS4{key}".encode(), date_stamp.encode())
    k_region = hmac_sha256(k_date, region.encode())
    k_service = hmac_sha256(k_region, service.encode())
    return hmac_sha256(k_service, b"aws4_request")

def upload(filepath: str, key: str):
    creds_file = Path.home() / ".aws" / "credentials"
    if not creds_file.exists():
        print("Error: ~/.aws/credentials not found")
        sys.exit(1)

    access_key = None
    secret_key = None
    for line in creds_file.read_text().splitlines():
        if line.startswith("aws_access_key_id"):
            access_key = line.split("=", 1)[1].strip()
        elif line.startswith("aws_secret_access_key"):
            secret_key = line.split("=", 1)[1].strip()

    if not access_key or not secret_key:
        print("Error: credentials not found in ~/.aws/credentials")
        sys.exit(1)

    body = Path(filepath).read_bytes()
    body_sha = sha256(body)
    content_type = "application/gzip"
    amz_date = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    date_stamp = amz_date[:8]
    service = "s3"

    # Canonical request
    canonical_uri = f"/{key}"
    canonical_querystring = ""
    headers = {
        "host": f"{BUCKET}.{ENDPOINT.removeprefix('https://')}",
        "x-amz-content-sha256": body_sha,
        "x-amz-date": amz_date,
    }
    signed_headers = ";".join(sorted(h.lower() for h in headers))
    canonical_headers = "".join(f"{h.lower()}:{headers[h]}\n" for h in sorted(headers))

    canonical_request = f"PUT\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{body_sha}"
    credential_scope = f"{date_stamp}/{REGION}/{service}/aws4_request"
    string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n{sha256(canonical_request.encode())}"

    signing_key = get_signature_key(secret_key, date_stamp, REGION, service)
    signature = hmac_sha256(signing_key, string_to_sign.encode()).hex()
    authorization = f"AWS4-HMAC-SHA256 Credential={access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"

    # Send request
    url = f"https://{BUCKET}.{ENDPOINT.removeprefix('https://')}{canonical_uri}"
    req = urllib.request.Request(url, data=body, method="PUT")
    req.add_header("Content-Type", content_type)
    req.add_header("Content-Length", str(len(body)))
    req.add_header("x-amz-content-sha256", body_sha)
    req.add_header("x-amz-date", amz_date)
    req.add_header("Authorization", authorization)

    try:
        resp = urllib.request.urlopen(req)
        print(f"OK  {key}  ({len(body)/1024/1024:.0f} MB)  [{resp.status}]")
    except urllib.error.HTTPError as e:
        print(f"ERR {key}  [{e.code}] {e.read().decode()[:200]}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: r2-upload.py <local_file> <s3_key>")
        sys.exit(1)
    upload(sys.argv[1], sys.argv[2])

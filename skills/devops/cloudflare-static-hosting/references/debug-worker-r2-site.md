# Debugging a Live Worker+R2 Site

Full worked example based on the `study.starseas.org/llmharnessagent/` site fix.

## Architecture

```
study.starseas.org/llmharnessagent/*
  └─ CF Worker Route (zone: starseas.org)
       └─ deepseek-papers Worker (ES Module)
            └─ R2 bucket: deepseek-papers
                    │  index.html (deepseek site root)
                    │  zh/ en/ pdf/ thinking-md/
                    └─ llm/index.html ← the broken file
```

## Step by Step: Diagnosing a JS Syntax Error

### 1. User Reports: "Left sidebar is empty, console shows SyntaxError"

```
llmharnessagent:663 Uncaught SyntaxError: Unexpected identifier 't'
```

### 2. Fetch the page, confirm the error

```bash
curl -s "https://study.starseas.org/llmharnessagent/" | grep "Unexpected\|SyntaxError\|Isn"
```

Finds: `enTitle:'Memory Granularity Control: Stronger Isn't Always Better'`

The `'` in `Isn't` closes the single-quoted JS string early, making `t` an unexpected identifier.

### 3. Map the architecture

List Workers:

```bash
curl -s "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/scripts" \
  -H "X-Auth-Email: ${EMAIL}" -H "X-Auth-Key: ${API_KEY}"
```

# → finds `deepseek-papers` worker

List routes for the zone:

```bash
curl -s "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/workers/routes" \
  -H "X-Auth-Email: ${EMAIL}" -H "X-Auth-Key: ${API_KEY}"
```

# → finds `study.starseas.org/llmharnessagent*` → `deepseek-papers`

Get the Worker script:

```bash
curl -s "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/scripts/deepseek-papers" \
  -H "X-Auth-Email: ${EMAIL}" -H "X-Auth-Key: ${API_KEY}"
```

# → finds Worker serves from `env.DEEPSEEK_BUCKET` with key prefix `llm/`

Get Worker bindings:

```bash
curl -s "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/workers/scripts/deepseek-papers/bindings" \
  -H "X-Auth-Email: ${EMAIL}" -H "X-Auth-Key: ${API_KEY}"
```

# → finds R2 bucket `deepseek-papers`, binding name `DEEPSEEK_BUCKET`

### 4. Download the file from R2 via boto3

```python
import boto3
from botocore.config import Config

s3 = boto3.client('s3',
    endpoint_url='https://d0a9c688290c80b51d6d4605ba32160a.r2.cloudflarestorage.com',
    aws_access_key_id='${ACCESS_KEY}',
    aws_secret_access_key='${SECRET_KEY}',
    config=Config(signature_version='s3v4'),
    region_name='auto'
)

obj = s3.get_object(Bucket='deepseek-papers', Key='llm/index.html')
content = obj['Body'].read().decode('utf-8')

# Find the bug
line = [l for l in content.split('\n') if 'id:12' in l][0]
print(line)
# → enTitle:'...Stronger Isn't Always Better...'
```

### 5. Fix: change single quotes to double quotes

The fix uses double-quote delimiters so the apostrophe inside is harmless:

```python
fixed = content.replace(
    "enTitle:'Memory Granularity Control: Stronger Isn't Always Better'",
    'enTitle:"Memory Granularity Control: Stronger Isn\'t Always Better"'
)

with open('/tmp/fixed_index.html', 'w') as f:
    f.write(fixed)
```

### 6. Upload back to R2

```python
with open('/tmp/fixed_index.html', 'rb') as f:
    resp = s3.put_object(
        Bucket='deepseek-papers',
        Key='llm/index.html',
        Body=f,
        ContentType='text/html; charset=utf-8',
        CacheControl='public, max-age=86400'
    )
print(resp['ResponseMetadata']['HTTPStatusCode'])  # 200 = OK
```

### 7. Purge CDN cache

```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/zones/f5264ddcfd4b8b524299c2e9f9cd55ec/purge_cache" \
  -H "X-Auth-Email: ${EMAIL}" -H "X-Auth-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"files":["https://study.starseas.org/llmharnessagent/"]}'
```

### 8. Verify

```bash
# Check the fix in the served response
curl -s "https://study.starseas.org/llmharnessagent/" | grep "id:12"
# → enTitle:"...Isn't..." (double quotes — safe)

# Open in browser and check for JS errors
# browser_console should show 0 errors
```

## Key Lessons

### JS String Delimiters in Inline Data

When embedding JavaScript data arrays directly in HTML:

| Delimiter | Risk | Safe With |
|-----------|------|-----------|
| `'...'` | Apostrophe/`'` inside the string breaks the script | No contractions/apostrophes |
| `"..."` | Double-quote inside breaks the script | No double quotes in values |
| Template literal `` `...` `` | Backtick/`${}` inside break the script | No backticks, no inline expressions |

**Rule of thumb**: If the data contains English contractions (`Isn't`, `Don't`, `Can't`, `It's`, etc.), use **double quotes** for the JS string or escape the apostrophe.

### Scan Before Deploy

```bash
# Find potential single-quote issues in single-quoted JS strings
grep -n "n't\\|'s\\|'re\\|'ll\\|'ve\\|'d\\|'m" index.html | grep -v "\\\\'" | head
```

### Reading Worker Multipart Responses

When fetching a Worker script via API, the response is **multipart**. Extract the script content:

```python
import re
# Response contains multipart with worker.mjs or similar
m = re.search(r'worker\.mjs.*?\n(.+?)(?:\n--|$)', http_body, re.DOTALL)
if m:
    script = m.group(1)
```

### Account-Specific Values (deepseek-papers)

| Parameter | Value |
|-----------|-------|
| Account ID | `d0a9c688290c80b51d6d4605ba32160a` |
| Zone ID (starseas.org) | `f5264ddcfd4b8b524299c2e9f9cd55ec` |
| Worker name | `deepseek-papers` |
| R2 bucket | `deepseek-papers` |
| R2 key prefix (llmharness) | `llm/` |
| Route pattern | `study.starseas.org/llmharnessagent*` |
| R2 access key | `REMOVED-R2-ACCESS-KEY-ID` |
| R2 secret key | (from user's R2 token) |

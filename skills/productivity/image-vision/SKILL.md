---
name: image-vision
description: Extract text (OCR) and describe content from images. Uses local Tesseract for free, unlimited text extraction. Optionally leverages Google Gemini Flash (free tier) for vision-language understanding. Use when the user sends an image that needs to be read, or when you need to understand what's in a screenshot/photo.
---

# Image Vision — OCR + VL Understanding

Extract text from images and/or describe their visual content. Two-layer architecture:

| Layer | Tool | What it does | Cost |
|-------|------|-------------|------|
| **OCR (text extraction)** | Tesseract (local) | Extract printed/handwritten text | **Free, unlimited** |
| **VL (image understanding)** | Gemini 2.0 Flash API | Describe image content in natural language | **Free tier: 1,500 req/day** |

The skill auto-detects available backends. Gemini is optional — OCR works standalone.

## When to Use

- User sends an image in chat → call `python3 ~/.hermes/skills/media/image-vision/scripts/vision.py <image_path>`
- User asks "what does this image say" → mode=ocr (default)
- User asks "describe this image" or the image has no text → mode=describe
- Screenshot from browser → extract text or understand the UI

## Agent Usage (when user sends image in Feishu)

**This is the most important workflow.** When the user sends an image from Feishu:

1. The image arrives as a media attachment with a local file path
2. IMMEDIATELY run OCR on it:
```bash
python3 ~/.hermes/skills/media/image-vision/scripts/vision.py <image_path> --mode ocr
```
3. If OCR confidence is > 50%, include the extracted text in your response
4. If OCR confidence is < 50% or text is too short (< 10 chars):
   - Run with `--mode auto` which will try OCR then fall back to describe (if Gemini configured)
   - Or manually run `--mode describe` if you know the image has no text
5. NEVER skip OCR on images. The user explicitly said: "所有发给我的文章，都要阅读图片里的内容，不要略过图片"

Fast one-liner to extract text from an image and format it:
```bash
python3 ~/.hermes/skills/media/image-vision/scripts/vision.py <image_path> --mode ocr --raw 2>/dev/null || echo "(OCR failed)"
```

## Quick Start

```bash
# OCR only (default) — extract all text
python3 ~/.hermes/skills/media/image-vision/scripts/vision.py /path/to/image.png

# Describe image content (requires Gemini API key)
python3 ~/.hermes/skills/media/image-vision/scripts/vision.py /path/to/image.png --mode describe

# Auto mode: OCR first, fall back to describe if no text found
python3 ~/.hermes/skills/media/image-vision/scripts/vision.py /path/to/image.png --mode auto

# Specify language for OCR (default: chi_sim+eng)
python3 ~/.hermes/skills/media/image-vision/scripts/vision.py /path/to/image.png --lang eng

# Force remote OCR (OCR.space) instead of tesseract
python3 ~/.hermes/skills/media/image-vision/scripts/vision.py /path/to/image.png --backend ocrspace
```

## Setup

### 1. Tesseract OCR (required for OCR mode)

Already installed on this machine (v5.3.4 with chi_sim + eng).

To add more languages:
```bash
sudo apt install tesseract-ocr-{jpn,kor,fra,deu,spa}  # etc.
```

### 2. Gemini API Key (optional, for describe mode)

**This is the ONLY free VL backend. Without it, image understanding is unavailable (OCR still works).**

1. Go to https://aistudio.google.com/apikey
2. Click "Create API Key" (new key = fresh 1,500 req/day quota)
3. Set it:
```bash
echo 'GEMINI_API_KEY=your-new-key-here' >> ~/.hermes/.env
```

**Free tier limits:** 1,500 requests/day, 1 request/second. Uses `gemini-2.0-flash` model.

**⚠️ Quota exhaustion:** When Gemini returns 429 "limit: 0", the free tier for that key is fully consumed. Get a new key from AI Studio. This is per-key, not per-account — creating a new key instantly resets quota.

### 3. OCR.space API Key (optional fallback)

1. Register at https://ocr.space/ocrapi/freekey
2. Set it:
```bash
echo 'OCR_SPACE_API_KEY=your-key-here' >> ~/.hermes/.env
```

**Free tier limits:** 500 requests/day, 25,000/month, 1MB file size.

## Output Format

All modes return JSON to stdout:
```json
{
  "mode": "ocr",
  "backend": "tesseract",
  "text": "extracted text here...",
  "confidence": 85.5,
  "language": "chi_sim+eng"
}
```

For describe mode:
```json
{
  "mode": "describe",
  "backend": "gemini",
  "description": "A screenshot showing a terminal window with...",
  "text_found": "any text visible in the image..."
}
```

## Script Reference

Full script: `scripts/vision.py`

Key functions:
- `ocr_tesseract(image_path, lang)` — Local OCR via pytesseract
- `ocr_ocrspace(image_path, lang)` — Remote OCR via OCR.space API
- `describe_gemini(image_path, prompt)` — VL understanding via Gemini
- `process_image(image_path, mode, backend, lang)` — Main entry point

## Degradation Behavior

When Gemini is unavailable (quota exhausted, network error):
- `--mode ocr` → Works normally (Tesseract is local)
- `--mode describe` → Returns error with actionable message
- `--mode auto` → Falls back to OCR-only, adds `fallback_reason` in output

**Agent rule:** Always try `--mode auto` first. If `fallback_reason` is present, the image has no extractable text AND Gemini is down — you'll need to describe the image from its filename/context or ask the user.

## Direct API Workaround (when vision_analyze fails)

When `vision_analyze` fails repeatedly (server disconnect, timeout, or auxiliary vision misconfigured), **bypass Hermes and call the provider API directly with base64**. This works because many providers (including opencodego) DO support image input — the issue is Hermes not injecting the image into the model's context.

```python
import base64, json, os, requests

img_path = "/path/to/image.jpg"
with open(img_path, "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

api_key = os.environ.get("OPENCODEGO_API_KEY", "")  # or appropriate key
url = "https://opencode.ai/zen/go/v1/chat/completions"  # or provider's endpoint

payload = {
    "model": "mimo-v2.5",  # or whichever model
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "用中文详细描述这张图片的所有内容"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
        ]
    }],
    "max_tokens": 2000
}

resp = requests.post(url, json=payload,
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    timeout=120)
print(resp.json()["choices"][0]["message"]["content"])
```

**When to use this:** vision_analyze fails 3+ times, auxiliary vision has no API key, or you need to verify a model actually supports vision input.

## Pitfalls

- **Tesseract needs pre-processing for best results**: Low-contrast or noisy images may produce poor OCR. The script auto-applies some preprocessing (grayscale, thresholding).
- **Gemini free tier rate limit**: 1 req/sec max. The script handles this but large batches will be slow.
- **OCR.space free tier**: 1MB file size limit. Images larger than this will be auto-resized.
- **Language detection**: Tesseract `--lang` parameter is a hint, not auto-detection. For mixed Chinese/English content, use `chi_sim+eng` (default).
- **Screenshots from Feishu**: Feishu images work directly — just pass the downloaded path.
- **Chinese social media screenshots**: Regular English-only OCR produces garbage on Chinese text. ALWAYS use `lang='chi_sim+eng'` for screenshots from WeChat, Weibo, Xiaohongshu, or any Chinese platform. If `vision_analyze` fails (network), fall back to pytesseract with Chinese language pack — NOT English-only.
- **Region-based OCR for better results**: For tall screenshots (e.g., 1080x2400 phone captures), crop into regions (top/middle/bottom) before OCR. Tesseract performs better on smaller, focused text regions than on full-page screenshots. Use PIL `img.crop((x1, y1, x2, y2))` to extract sections.
- **Use the vision.py script first**: Before falling back to raw pytesseract, always try `python3 ~/.hermes/skills/media/image-vision/scripts/vision.py <path> --mode ocr`. The script has preprocessing (grayscale, thresholding, noise reduction) that raw pytesseract lacks.

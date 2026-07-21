#!/usr/bin/env python3
"""
Image Vision — OCR and Vision-Language understanding for Hermes Agent.

Modes:
  ocr       — Extract text from image (tesseract local or OCR.space remote)
  describe  — Describe image content in natural language (Gemini VL)
  auto      — OCR first, fall back to describe if no useful text found

Backends:
  tesseract — Local OCR (free, unlimited, needs tesseract installed)
  ocrspace  — Remote OCR via OCR.space API (free tier: 500/day)
  gemini    — Google Gemini 2.0 Flash VL (free tier: 1,500/day)

Usage:
  python3 vision.py <image_path> [--mode ocr|describe|auto] [--lang chi_sim+eng] [--backend tesseract|ocrspace]
"""

import argparse
import base64
import json
import os
import sys
import tempfile
from pathlib import Path

import requests
from PIL import Image

# ── Config ──────────────────────────────────────────────────────


def load_env():
    """Load API keys from ~/.hermes/.env and ~/.env."""
    env_paths = [
        Path.home() / ".hermes" / ".env",
        Path.home() / ".env",
    ]
    for p in env_paths:
        if p.exists():
            with open(p) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ.setdefault(key.strip(), val.strip())


load_env()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OCR_SPACE_API_KEY = os.environ.get("OCR_SPACE_API_KEY", "")
# OCR.space free-tier key works without API key too (just uses default 'helloworld')
OCR_SPACE_DEFAULT_KEY = "helloworld"

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
OCR_SPACE_URL = "https://api.ocr.space/parse/image"


# ── Image Preprocessing ─────────────────────────────────────────


def preprocess_for_ocr(image_path: str) -> str:
    """
    Minimal preprocessing for OCR. Tesseract works best on clean, unmodified
    screenshots. Aggressive filtering (sharpening, thresholding, blur) hurts
    accuracy on anti-aliased text — the most common case.
    
    Only handles color mode conversion (RGBA→RGB, P→RGB).
    Returns path to temp image (or original if no conversion needed).
    """
    img = Image.open(image_path)
    original_mode = img.mode

    # Convert transparent / palette modes to flat RGB
    if img.mode in ("RGBA", "P", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = background
    elif img.mode != "RGB" and img.mode != "L":
        img = img.convert("RGB")

    if img.mode == original_mode and original_mode in ("RGB", "L"):
        # No conversion needed — use original
        return image_path

    # Save converted image to temp file
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name, "PNG")
    return tmp.name


# ── OCR Backends ────────────────────────────────────────────────


def ocr_tesseract(image_path: str, lang: str = "chi_sim+eng") -> dict:
    """Local OCR using pytesseract (wrapper around tesseract CLI)."""
    try:
        import pytesseract
    except ImportError:
        return {"error": "pytesseract not installed. Run: pip install pytesseract"}

    preprocessed = preprocess_for_ocr(image_path)
    used_temp = (preprocessed != image_path)

    try:
        # Get text
        text = pytesseract.image_to_string(
            Image.open(preprocessed), lang=lang, config="--psm 3"
        )

        # Get confidence data
        data = pytesseract.image_to_data(
            Image.open(preprocessed), lang=lang, output_type=pytesseract.Output.DICT
        )
        confidences = [
            int(c) for c in data["conf"] if c != "-1" and int(c) > 0
        ]
        avg_confidence = round(sum(confidences) / len(confidences), 1) if confidences else 0

        # Trim whitespace
        text = text.strip()

        return {
            "mode": "ocr",
            "backend": "tesseract",
            "text": text,
            "confidence": avg_confidence,
            "language": lang,
            "word_count": len(text.split()) if text else 0,
            "char_count": len(text),
        }
    finally:
        # Clean up temp file only if we created one
        if used_temp:
            try:
                os.unlink(preprocessed)
            except OSError:
                pass


def ocr_ocrspace(image_path: str, lang: str = "chs") -> dict:
    """Remote OCR via OCR.space free API."""
    api_key = OCR_SPACE_API_KEY or OCR_SPACE_DEFAULT_KEY

    # OCR.space language codes
    lang_map = {
        "chi_sim": "chs",
        "chi_sim+eng": "chs",
        "eng": "eng",
        "jpn": "jpn",
        "kor": "kor",
        "fra": "fre",
        "deu": "ger",
        "spa": "spa",
    }
    ocr_lang = lang_map.get(lang, "eng")

    # Check file size (free tier: 1MB)
    file_size = os.path.getsize(image_path)
    if file_size > 1_000_000:
        # Resize image to fit within 1MB
        img = Image.open(image_path)
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        quality = 85
        while quality > 10:
            img.save(tmp.name, "JPEG", quality=quality)
            if os.path.getsize(tmp.name) < 1_000_000:
                break
            quality -= 10
        image_path = tmp.name

    try:
        with open(image_path, "rb") as f:
            payload = {
                "apikey": api_key,
                "language": ocr_lang,
                "isOverlayRequired": False,
                "filetype": "auto",
                "OCREngine": 2,  # Engine 2 = more accurate
            }
            files = {"file": f}
            resp = requests.post(
                OCR_SPACE_URL, data=payload, files=files, timeout=60
            )
            resp.raise_for_status()
            result = resp.json()

        if result.get("IsErroredOnProcessing"):
            return {"error": result.get("ErrorMessage", "OCR.space processing error")}

        parsed = result.get("ParsedResults", [])
        if not parsed:
            return {"error": "No results from OCR.space"}

        text = parsed[0].get("ParsedText", "").strip()
        exit_code = parsed[0].get("FileParseExitCode", -1)

        return {
            "mode": "ocr",
            "backend": "ocrspace",
            "text": text,
            "confidence": None,  # OCR.space doesn't report per-word confidence easily
            "language": ocr_lang,
            "word_count": len(text.split()) if text else 0,
            "char_count": len(text),
            "exit_code": exit_code,
        }
    finally:
        # Clean up temp file if we created one
        if image_path.endswith(".jpg") and "tmp" in image_path:
            try:
                os.unlink(image_path)
            except OSError:
                pass


# ── VL Backend ──────────────────────────────────────────────────


def describe_gemini(image_path: str, prompt: str = None) -> dict:
    """Describe image content using Google Gemini 2.0 Flash (free tier)."""
    if not GEMINI_API_KEY:
        return {"error": "GEMINI_API_KEY not set. Get free key at https://aistudio.google.com/apikey"}

    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # Detect MIME type
    ext = Path(image_path).suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }
    mime_type = mime_map.get(ext, "image/png")

    if prompt is None:
        prompt = (
            "Please analyze this image in detail. "
            "1) List ALL text visible in the image exactly as it appears (including any Chinese, English, or other language text). "
            "2) Describe what the image shows — the scene, objects, colors, layout, and any notable details. "
            "3) If this is a UI screenshot, describe the interface elements and their purposes. "
            "Format your response with clear sections."
        )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_data,
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 2048,
        },
    }

    resp = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        json=payload,
        timeout=90,
    )

    if resp.status_code == 429:
        return {"error": "Gemini rate limited (1 req/sec max). Wait and retry."}
    if resp.status_code != 200:
        return {"error": f"Gemini API error: {resp.status_code} — {resp.text[:300]}"}

    result = resp.json()
    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        if "error" in result:
            return {"error": f"Gemini: {result['error'].get('message', 'unknown error')}"}
        return {"error": f"Unexpected Gemini response: {json.dumps(result)[:500]}"}

    return {
        "mode": "describe",
        "backend": "gemini",
        "description": text.strip(),
        "prompt_used": prompt,
    }


# ── Main Processing ─────────────────────────────────────────────


def process_image(image_path: str, mode: str = "ocr", backend: str = "tesseract", lang: str = "chi_sim+eng") -> dict:
    """
    Process an image and return structured results.

    Args:
        image_path: Path to image file (PNG, JPG, WEBP, BMP supported)
        mode: 'ocr' (text extraction), 'describe' (VL understanding), 'auto' (smart choice)
        backend: 'tesseract' (local), 'ocrspace' (remote API)
        lang: Tesseract language code (ignored for Gemini mode)

    Returns:
        dict with mode-specific results + optional error key
    """
    # Validate file exists
    if not os.path.isfile(image_path):
        return {"error": f"File not found: {image_path}"}

    # Check file is an image
    try:
        Image.open(image_path).verify()
    except Exception:
        return {"error": f"Not a valid image file: {image_path}"}

    # Auto mode: Try OCR first, if no useful text, try describe
    if mode == "auto":
        # Try OCR
        ocr_result = ocr_tesseract(image_path, lang)
        if "error" in ocr_result:
            # OCR failed entirely — try describe as last resort
            if GEMINI_API_KEY:
                desc = describe_gemini(image_path)
                if "error" not in desc:
                    return desc
            # Both failed
            ocr_result["fallback_reason"] = "OCR failed, Gemini unavailable"
            return ocr_result

        text = ocr_result.get("text", "")
        # If OCR found meaningful text (more than just a few chars), return it
        if len(text) > 20:
            return ocr_result

        # OCR found little/no text — try describe for visual understanding
        if GEMINI_API_KEY:
            desc_result = describe_gemini(image_path)
            if "error" not in desc_result:
                desc_result["ocr_text"] = text if text else "(no text found)"
                return desc_result
            # Gemini failed too — fall back to OCR-only with reason
            ocr_result["fallback_reason"] = f"Little text found ({len(text)} chars), Gemini unavailable: {desc_result.get('error', 'unknown')}"
            return ocr_result

        # No Gemini configured — just return OCR
        if len(text) <= 20:
            ocr_result["fallback_reason"] = f"Little text found ({len(text)} chars), no VL backend configured"
        return ocr_result

    # OCR mode
    if mode == "ocr":
        if backend == "ocrspace":
            return ocr_ocrspace(image_path, lang)
        return ocr_tesseract(image_path, lang)

    # Describe mode
    if mode == "describe":
        return describe_gemini(image_path)

    return {"error": f"Unknown mode: {mode}. Use 'ocr', 'describe', or 'auto'."}


# ── CLI ─────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Image Vision — OCR and VL understanding for Hermes Agent"
    )
    parser.add_argument("image", help="Path to image file")
    parser.add_argument(
        "--mode",
        choices=["ocr", "describe", "auto"],
        default="ocr",
        help="Processing mode (default: ocr)",
    )
    parser.add_argument(
        "--backend",
        choices=["tesseract", "ocrspace"],
        default="tesseract",
        help="OCR backend (default: tesseract)",
    )
    parser.add_argument(
        "--lang",
        default="chi_sim+eng",
        help="Tesseract language code (default: chi_sim+eng)",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Custom prompt for describe mode (Gemini only)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Output only the extracted text/description, no JSON wrapper",
    )

    args = parser.parse_args()

    result = process_image(args.image, args.mode, args.backend, args.lang)

    if args.raw:
        if "text" in result:
            print(result["text"])
        elif "description" in result:
            print(result["description"])
        elif "error" in result:
            print(f"ERROR: {result['error']}", file=sys.stderr)
            sys.exit(1)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    if "error" in result and not args.raw:
        sys.exit(1)


if __name__ == "__main__":
    main()

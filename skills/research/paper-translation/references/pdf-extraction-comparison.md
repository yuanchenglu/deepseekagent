# PDF Text Extraction Tools for Paper Translation

Comparison based on real usage during June 2026 paper translation session.

## Summary

| Tool | Text Spacing | Table Detection | Speed | Verdict |
|------|-------------|----------------|-------|---------|
| **PyMuPDF (fitz)** | ✅ Excellent | ✅ Good (find_tables) | Fast | **BEST CHOICE** |
| **pypdf** | ❌ Poor (words concatenated) | ❌ None | Fast | Use only if PyMuPDF unavailable |
| **pdfplumber** | ⚠️ Decent | ✅ Good (find_tables) | Medium | Better than pypdf, but PyMuPDF is better |
| **marker-pdf** | ✅ Excellent | ✅ Excellent | Very slow (model download >120s) | Overkill for text extraction |

## PyMuPDF (Recommended)

```bash
pip install PyMuPDF
```

Key flags:
- `fitz.TEXT_PRESERVE_WHITESPACE` — critical flag for proper word spacing
- `page.find_tables()` — built-in table detection
- `page.get_text("dict", flags=...)` — block-level extraction with position data

## pypdf (Not Recommended)

```bash
pip install pypdf
```

Major issue: text extracted without spaces between words.
- "Therapiddevelopmentofopen-sourcelargelanguagemodels" instead of "The rapid development of open-source large language models"
- Tables are completely flattened to text

## marker-pdf (Too Slow for Practical Use)

```bash
pip install marker-pdf
```

Downloads vision models on first conversion attempt. Timed out at >120 seconds in testing. Good output quality but impractical without pre-cached models.

## Nature Journal PDFs

Nature PDFs use nonstandard encoding:
- `pypdf` fails with "Stream has ended unexpectedly"
- `PyMuPDF` also fails with "No /Root object!"
- **Fix:** Download from arXiv if available (e.g., ChemCrow: arxiv.org/pdf/2304.05376) or download from nature.com's PDF endpoint

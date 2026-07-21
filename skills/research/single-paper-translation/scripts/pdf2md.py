#!/usr/bin/env python3
"""Better PDF to Markdown using PyMuPDF (fitz) with table detection.
Usage: python3 pdf2md.py <input.pdf> <output.md>
"""
import sys, os
import fitz  # PyMuPDF

pdf_path = sys.argv[1]
md_path = sys.argv[2]

doc = fitz.open(pdf_path)
page_count = doc.page_count  # ⚠️ must read before doc.close()!
md_lines = []

for i, page in enumerate(doc):
    md_lines.append(f"\n<!-- Page {i+1} -->\n")
    
    # Try to find tables via PyMuPDF built-in detector
    tables = page.find_tables()
    
    # Get text blocks with position info for better layout
    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
    
    # Collect text and detect table areas
    text_parts = []
    table_regions = []
    
    if tables and tables.tables:
        for t in tables.tables:
            table_regions.append((t.bbox, t.extract()))
    
    # Process blocks, skip those inside tables (render tables separately)
    for block in blocks:
        if block["type"] == 0:  # text block
            bbox = block["bbox"]
            in_table = False
            for t_bbox, _ in table_regions:
                if (bbox[0] >= t_bbox[0] and bbox[1] >= t_bbox[1] and 
                    bbox[2] <= t_bbox[2] and bbox[3] <= t_bbox[3]):
                    in_table = True
                    break
            if not in_table:
                for line in block["lines"]:
                    text = " ".join([span["text"] for span in line["spans"]])
                    if text.strip():
                        text_parts.append(text)
    
    if text_parts:
        md_lines.append("\n".join(text_parts))
    
    # Render detected tables as Markdown tables
    for t_bbox, t_data in table_regions:
        if t_data and len(t_data) > 0:
            md_lines.append("\n")
            header = t_data[0]
            md_lines.append("| " + " | ".join([str(c or "").replace("\n", " ") for c in header]) + " |")
            md_lines.append("| " + " | ".join(["---"] * len(header)) + " |")
            for row in t_data[1:]:
                md_lines.append("| " + " | ".join([str(c or "").replace("\n", " ") for c in row]) + " |")
            md_lines.append("")
    
    md_lines.append("\n---\n")

doc.close()

output = "\n".join(md_lines)
with open(md_path, 'w') as f:
    f.write(output)

lines = output.split('\n')
table_count = sum(1 for l in lines if l.startswith('|---'))
print(f"Done: {len(output)} chars, {len(lines)} lines, {page_count} pages, ~{table_count} table rows")

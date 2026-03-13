---
name: pdf-reader
description: Use this skill when the user wants to read, parse, or extract data from PDF files — text, tables, images, or metadata.
---

# PDF Reader

## Overview

Extracts text, tables, images, and metadata from PDF files. Handles text-based and scanned (OCR) PDFs. Uses pdfplumber for tables, pymupdf for speed, and pytesseract for scanned documents.

## Quick Start — Extract All Text

```python
import pdfplumber

def extract_text(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        return "\n\n".join(
            page.extract_text() or "" for page in pdf.pages
        )
```

## Extract Tables

```python
import pdfplumber
import pandas as pd

def extract_tables(pdf_path: str, page_num: int | None = None) -> list[pd.DataFrame]:
    """Extract all tables from PDF as DataFrames."""
    dfs = []
    with pdfplumber.open(pdf_path) as pdf:
        pages = [pdf.pages[page_num]] if page_num is not None else pdf.pages
        for page in pages:
            for table in page.extract_tables():
                if table and table[0]:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    dfs.append(df)
    return dfs

def tables_to_csv(pdf_path: str, output_dir: str = ".") -> list[str]:
    from pathlib import Path
    Path(output_dir).mkdir(exist_ok=True)
    paths = []
    for i, df in enumerate(extract_tables(pdf_path)):
        out = f"{output_dir}/table_{i+1}.csv"
        df.to_csv(out, index=False)
        paths.append(out)
    return paths
```

## Fast Extraction with pymupdf

```python
import fitz  # pip install pymupdf

def extract_text_fast(pdf_path: str) -> str:
    """10-50x faster than pdfplumber for text-only extraction."""
    doc = fitz.open(pdf_path)
    return "\n\n".join(page.get_text() for page in doc)

def extract_page_range(pdf_path: str, start: int, end: int) -> str:
    """Extract text from pages start..end (0-indexed)."""
    doc = fitz.open(pdf_path)
    return "\n\n".join(doc[i].get_text() for i in range(start, min(end, len(doc))))

def get_metadata(pdf_path: str) -> dict:
    doc = fitz.open(pdf_path)
    return {**doc.metadata, "pages": len(doc)}
```

## Extract Images

```python
import fitz
from pathlib import Path

def extract_images(pdf_path: str, output_dir: str = "extracted_images") -> list[str]:
    Path(output_dir).mkdir(exist_ok=True)
    doc = fitz.open(pdf_path)
    saved = []
    for page_num, page in enumerate(doc):
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            ext = base_image["ext"]
            out = f"{output_dir}/page{page_num+1}_img{img_index+1}.{ext}"
            Path(out).write_bytes(base_image["image"])
            saved.append(out)
    return saved
```

## OCR for Scanned PDFs

```python
from pdf2image import convert_from_path
import pytesseract

def ocr_pdf(pdf_path: str, lang: str = "eng") -> str:
    """Extract text from a scanned PDF using OCR."""
    images = convert_from_path(pdf_path, dpi=300)
    pages = []
    for i, img in enumerate(images):
        text = pytesseract.image_to_string(img, lang=lang)
        pages.append(f"--- Page {i+1} ---\n{text}")
    return "\n\n".join(pages)

def is_text_pdf(pdf_path: str) -> bool:
    """Returns True if PDF has selectable text (not scanned)."""
    with pdfplumber.open(pdf_path) as pdf:
        return any(page.extract_text() for page in pdf.pages[:3])
```

## Multi-Column Layout

```python
import pdfplumber

def extract_two_column(pdf_path: str) -> str:
    """Handle 2-column academic/newspaper layouts."""
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            w = page.width
            left = page.crop((0, 0, w/2, page.height))
            right = page.crop((w/2, 0, w, page.height))
            text_parts.append(left.extract_text() or "")
            text_parts.append(right.extract_text() or "")
    return "\n\n".join(t for t in text_parts if t.strip())
```

## Quick Reference

| Task | Library | Notes |
|------|---------|-------|
| Extract text | pdfplumber or pymupdf | pymupdf faster |
| Extract tables | pdfplumber | Returns nested lists |
| Tables → DataFrame | pdfplumber + pandas | Then `.to_csv()` |
| Extract images | pymupdf (fitz) | Returns bytes |
| Scanned PDF | pdf2image + pytesseract | Needs tesseract installed |
| Check if scanned | pdfplumber | Check for empty text |
| Metadata | pymupdf | `.metadata` dict |

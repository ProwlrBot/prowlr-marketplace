---
name: pdf-analysis
description: Use this skill when the user wants to analyze, summarize, extract data from, or ask questions about PDF documents using Claude's native PDF support.
source: https://github.com/anthropics/anthropic-cookbook/tree/main/multimodal/pdf_support
---

# PDF Analysis

## Overview

Claude natively supports PDF documents — send the PDF as a document block and Claude reads the full content including text, tables, and layout-aware formatting. No pre-processing required for most documents.

## Basic PDF Analysis

```python
import anthropic
import base64
from pathlib import Path

client = anthropic.Anthropic()

def analyze_pdf(pdf_path: str, question: str) -> str:
    pdf_data = base64.b64encode(Path(pdf_path).read_bytes()).decode("utf-8")

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data,
                    }
                },
                {
                    "type": "text",
                    "text": question
                }
            ],
        }],
    )
    return response.content[0].text
```

## Document Summarization

```python
def summarize_pdf(pdf_path: str, style: str = "executive") -> str:
    prompts = {
        "executive": "Provide a 3-paragraph executive summary: key findings, implications, recommended actions.",
        "bullet": "List the 10 most important points from this document as bullet points.",
        "detailed": "Provide a comprehensive section-by-section summary.",
    }
    return analyze_pdf(pdf_path, prompts.get(style, prompts["executive"]))
```

## Table Extraction

```python
def extract_tables(pdf_path: str) -> str:
    return analyze_pdf(
        pdf_path,
        """Extract all tables from this document.
        Format each table as markdown.
        Label each table with a title if visible in the document."""
    )
```

## Multi-Document Comparison

```python
def compare_pdfs(pdf_paths: list[str], comparison_question: str) -> str:
    content = []
    for i, path in enumerate(pdf_paths, 1):
        pdf_data = base64.b64encode(Path(path).read_bytes()).decode("utf-8")
        content.append({
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_data},
            "title": f"Document {i}: {Path(path).name}",
        })
    content.append({"type": "text", "text": comparison_question})

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": content}],
    )
    return response.content[0].text
```

## URL-Based PDFs

```python
def analyze_pdf_url(url: str, question: str) -> str:
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {"type": "url", "url": url}
                },
                {"type": "text", "text": question}
            ],
        }],
    )
    return response.content[0].text
```

## Quick Reference

| Task | Approach |
|------|----------|
| Single PDF Q&A | `analyze_pdf(path, question)` |
| Summarize | `summarize_pdf(path, style)` |
| Extract tables | `extract_tables(path)` |
| Compare docs | `compare_pdfs([p1, p2], question)` |
| URL PDF | `analyze_pdf_url(url, question)` |
| Max pages | ~100 pages per document |

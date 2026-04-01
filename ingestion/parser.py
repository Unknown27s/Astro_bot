"""
IMS AstroBot — Document Parsers
Extracts text from PDF, DOCX, TXT, XLSX, CSV, PPTX, and HTML files.
"""

import os
import csv
import io
from pathlib import Path
from typing import Optional


def parse_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    from PyPDF2 import PdfReader

    try:
        reader = PdfReader(file_path)

        # Check if PDF is encrypted/locked
        if reader.is_encrypted:
            # Try to decrypt with empty password (common for read-only PDFs)
            if not reader.decrypt(""):
                raise ValueError(
                    "PDF is password-protected or encrypted. "
                    "Please remove the password/encryption using Adobe Reader or similar tool, "
                    "and try uploading again."
                )

        text_parts = []
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"[Page {page_num}]\n{page_text}")
        return "\n\n".join(text_parts)
    except ValueError as e:
        # Re-raise ValueError for encrypted PDFs (handled in parse_document)
        raise
    except Exception as e:
        # Other PDF reading errors
        raise


def parse_docx(file_path: str) -> str:
    """Extract text from a DOCX file, preserving heading structure."""
    from docx import Document

    doc = Document(file_path)
    text_parts = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        # Mark headings for structural chunking
        if para.style and para.style.name.startswith("Heading"):
            level = para.style.name.replace("Heading ", "").strip()
            text_parts.append(f"\n{'#' * int(level) if level.isdigit() else '##'} {text}\n")
        else:
            text_parts.append(text)
    return "\n".join(text_parts)


def parse_txt(file_path: str) -> str:
    """Read a plain text file."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    # Fallback with error replacement
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def parse_xlsx(file_path: str) -> str:
    """Extract text from an Excel file (all sheets)."""
    from openpyxl import load_workbook

    wb = load_workbook(file_path, read_only=True, data_only=True)
    text_parts = []
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        text_parts.append(f"\n## Sheet: {sheet_name}\n")
        for row in ws.iter_rows(values_only=True):
            cells = [str(cell) if cell is not None else "" for cell in row]
            line = " | ".join(cells).strip()
            if line and line != "| " * len(cells):
                text_parts.append(line)
    wb.close()
    return "\n".join(text_parts)


def parse_csv(file_path: str) -> str:
    """Extract text from a CSV file."""
    text_parts = []
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        for row in reader:
            line = " | ".join(row).strip()
            if line:
                text_parts.append(line)
    return "\n".join(text_parts)


def parse_pptx(file_path: str) -> str:
    """Extract text from a PowerPoint file."""
    from pptx import Presentation

    prs = Presentation(file_path)
    text_parts = []
    for slide_num, slide in enumerate(prs.slides, 1):
        slide_texts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        slide_texts.append(text)
        if slide_texts:
            text_parts.append(f"[Slide {slide_num}]\n" + "\n".join(slide_texts))
    return "\n\n".join(text_parts)


def parse_html(file_path: str) -> str:
    """Extract text from an HTML file."""
    from bs4 import BeautifulSoup

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    # Remove script and style elements
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    text = soup.get_text(separator="\n", strip=True)
    # Clean up multiple blank lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


# ── File extension → parser mapping ──
PARSERS = {
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".txt": parse_txt,
    ".xlsx": parse_xlsx,
    ".csv": parse_csv,
    ".pptx": parse_pptx,
    ".html": parse_html,
    ".htm": parse_html,
}


def parse_document(file_path: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parse a document and return extracted text.
    Returns (text, None) on success, or (None, error_message) on failure.
    """
    ext = Path(file_path).suffix.lower()
    parser = PARSERS.get(ext)
    if not parser:
        return None, f"Unsupported file type: {ext}"
    try:
        text = parser(file_path)
        if not text or not text.strip():
            return None, "Document appears to be empty or contains no extractable text"
        return text.strip(), None
    except Exception as e:
        print(f"[Parser Error] {file_path}: {e}")
        return None, f"Failed to parse document: {str(e)}"

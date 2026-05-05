"""
Table extraction from PDFs and documents.

Extracts structured data (tables) from PDF pages and returns them
in a format suitable for vector storage and LLM context.

Supports:
  - PDFs via pdfplumber (native table detection)
  - Fallback: Manual table parsing from text patterns
"""

from __future__ import annotations

import re
from typing import NamedTuple


class ExtractedTable(NamedTuple):
    """Structured table data."""
    title: str  # e.g., "Table 4.1: Credit Assignment"
    headers: list[str]  # Column headers
    rows: list[list[str]]  # Data rows
    page: int  # Page number where table was found
    text: str  # Full text representation (for embedding)


def extract_tables_from_pdf(pdf_path: str) -> list[ExtractedTable]:
    """
    Extract tables from PDF using pdfplumber.
    
    Returns list of structured tables with headers, rows, and metadata.
    """
    try:
        import pdfplumber
    except ImportError:
        return []

    tables: list[ExtractedTable] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract native tables from page
                page_tables = page.extract_tables()

                if not page_tables:
                    continue

                for table_idx, table in enumerate(page_tables):
                    if not table:
                        continue

                    # First row is usually headers
                    headers = [str(cell or "").strip() for cell in table[0]]
                    rows = [
                        [str(cell or "").strip() for cell in row]
                        for row in table[1:]
                    ]

                    # Create title from context
                    title = f"Table {table_idx + 1} (Page {page_num})"

                    # Convert to text for embedding
                    text_repr = _table_to_text(headers, rows, title)

                    tables.append(
                        ExtractedTable(
                            title=title,
                            headers=headers,
                            rows=rows,
                            page=page_num,
                            text=text_repr,
                        )
                    )
    except Exception as e:
        print(f"[WARN] Error extracting tables from PDF: {e}")

    return tables


def _table_to_text(headers: list[str], rows: list[list[str]], title: str = "") -> str:
    """
    Convert table structure to readable text for embedding.
    
    Example output:
    Table 4.1: Credit Assignment
    Contact periods: 1 Lecture Period, Credit: 1
    Contact periods: 1 Tutorial Period, Credit: 1
    ...
    """
    lines = []

    if title:
        lines.append(title)
        lines.append("-" * 50)

    # Header
    if headers:
        lines.append(" | ".join(headers))
        lines.append("-" * 50)

    # Rows
    for row in rows:
        lines.append(" | ".join(row))

    return "\n".join(lines)


def detect_markdown_table(text: str) -> list[ExtractedTable]:
    """
    Fallback: Detect and parse markdown-style tables from text.
    
    Pattern:
    | Header1 | Header2 |
    |---------|---------|
    | Data1   | Data2   |
    """
    tables: list[ExtractedTable] = []

    # Pattern for markdown tables
    table_pattern = r'\|.*?\|[\n\r][\|\s-]+'

    matches = re.finditer(table_pattern, text, re.MULTILINE)

    for match in matches:
        table_text = match.group(0)
        lines = [
            line.strip()
            for line in table_text.split("\n")
            if line.strip() and not re.match(r'^[\|\s-]+$', line)
        ]

        if len(lines) < 2:
            continue

        # Parse headers
        header_line = lines[0]
        headers = [
            h.strip() for h in header_line.split("|") if h.strip()
        ]

        # Parse rows (skip separator line)
        rows = []
        for line in lines[2:]:  # Skip header + separator
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if cells:
                rows.append(cells)

        if headers and rows:
            tables.append(
                ExtractedTable(
                    title=f"Extracted Table (Auto-detected)",
                    headers=headers,
                    rows=rows,
                    page=0,  # Unknown page
                    text=_table_to_text(headers, rows),
                )
            )

    return tables


def format_table_for_llm(table: ExtractedTable) -> str:
    """
    Format table for LLM context with clear structure.
    
    Example:
    TABLE: Table 4.1 - Credit Assignment (Page 5)
    
    HEADERS: Contact periods | Credit
    
    ROWS:
    - 1 Lecture Period | 1
    - 1 Tutorial Period | 1
    - 2 Laboratory Periods | 1
    """
    lines = [
        f"TABLE: {table.title}",
        "",
        f"HEADERS: {' | '.join(table.headers)}",
        "",
        "ROWS:",
    ]

    for row in table.rows:
        lines.append(f"- {' | '.join(row)}")

    return "\n".join(lines)

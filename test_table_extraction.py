#!/usr/bin/env python
"""
Quick test of table extraction from PDF documents.

Shows extracted tables with metadata for structured data retrieval.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from ingestion.parser import extract_tables_with_metadata
from ingestion.table_extractor import format_table_for_llm


def main() -> int:
    # Test with the UG Regulations PDF
    pdf_path = "data/uploads"  # Look for uploaded documents
    
    # Find the first PDF
    pdf_files = list(Path(pdf_path).glob("*.pdf"))
    if not pdf_files:
        print("[ERROR] No PDF files found in data/uploads/")
        return 1

    pdf_file = pdf_files[0]
    print(f"[INFO] Extracting tables from: {pdf_file.name}\n")

    tables = extract_tables_with_metadata(str(pdf_file))

    if not tables:
        print("[WARN] No tables found in document")
        return 0

    print(f"[✓] Found {len(tables)} tables\n")

    for idx, table in enumerate(tables, 1):
        print("=" * 80)
        print(f"[TABLE {idx}] {table['title']}")
        print(f"  Type: {table['type']}")
        print(f"  Page: {table['page']}")
        print(f"  Size: {len(table['rows'])} rows × {len(table['headers'])} columns")
        print("=" * 80)
        print()

        # Show formatted table for LLM
        from ingestion.table_extractor import ExtractedTable
        
        table_obj = ExtractedTable(
            title=table['title'],
            headers=table['headers'],
            rows=table['rows'],
            page=table['page'],
            text=table['text']
        )
        
        formatted = format_table_for_llm(table_obj)
        print(formatted)
        print("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

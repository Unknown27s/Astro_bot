"""Manual helper to test retriever against one uploaded document only.

Usage examples (from project root):

python testing/scripts/test_retriever_single_doc.py --query "what is attendance policy" --doc-id <DOCUMENT_ID>
python testing/scripts/test_retriever_single_doc.py --query "fees" --filename policy.pdf
python testing/scripts/test_retriever_single_doc.py --query "hostel" --filename policy.pdf --top-k 5 --source-type uploaded
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

# Allow running as a standalone script from project root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from database.db import get_all_documents
from rag.retriever import retrieve_context


def _resolve_doc_id(doc_id: str | None, filename: str | None) -> str:
    if doc_id:
        return doc_id

    if not filename:
        raise ValueError("Provide either --doc-id or --filename")

    docs = get_all_documents()
    target = filename.strip().lower()

    for d in docs:
        original = str(d.get("original_name") or "").strip().lower()
        stored = str(d.get("filename") or "").strip().lower()
        if target in {original, stored}:
            return str(d["id"])

    raise ValueError(f"Document not found for filename: {filename}")


def _clean_pdf_text(text: str) -> str:
    """
    Clean fragmented PDF extraction text.
    Removes pipe characters, fixes broken words, normalizes whitespace.
    """
    # Remove pipe characters from PDF extraction artifacts
    text = text.replace(" | ", " ").replace("|", "")
    
    # Fix words broken across lines (e.g., "ester fo | r" → "ester for")
    # Common pattern: word_part1 space word_part2
    import re
    text = re.sub(r'(\w+)\s+(\w+)\s+(\w+)', lambda m: m.group(1) + m.group(2) + ' ' + m.group(3), text)
    
    # Normalize whitespace: multiple spaces → single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove excessive newlines
    text = text.replace('\n\n\n', '\n').replace('\n\n', '\n').strip()
    
    return text


def _retrieve_pages(
    query: str,
    doc_id: str,
    source_type: str = "uploaded",
    top_k: int = 5,
) -> list[dict]:
    """Retrieve and group chunks by page number to create full page context."""
    chunks = retrieve_context(
        query=query,
        top_k=top_k * 3,  # Get more chunks to ensure complete pages
        source_type=source_type,
        doc_id=doc_id,
    )

    if not chunks:
        return []

    # Group chunks by page number
    pages_dict: dict[int, dict] = defaultdict(lambda: {"text": "", "chunks": [], "score": 0})

    for chunk in chunks:
        # Extract page number from heading (e.g., "Page 5" → 5)
        heading = str(chunk.get("heading") or "")
        page_num = 0

        if "page " in heading.lower():
            parts = heading.lower().split("page ")
            if len(parts) > 1:
                try:
                    page_num = int(parts[1].split()[0])
                except (ValueError, IndexError):
                    pass

        if page_num == 0:
            # Fallback: try to extract from metadata
            page_num = chunk.get("page", 0)

        if page_num > 0:
            # Clean and add chunk text to page
            text = chunk.get("text", "")
            clean_text = _clean_pdf_text(text)
            pages_dict[page_num]["text"] += " " + clean_text
            pages_dict[page_num]["chunks"].append(chunk)

            # Use best score for this page
            score = chunk.get("score", 0)
            if score > pages_dict[page_num]["score"]:
                pages_dict[page_num]["score"] = score

    # Convert to sorted list, keeping top-k pages
    pages = []
    for page_num in sorted(pages_dict.keys()):
        page_data = pages_dict[page_num]
        clean_text = _clean_pdf_text(page_data["text"])
        pages.append({
            "page": page_num,
            "text": clean_text.strip(),
            "score": page_data["score"],
            "chunk_count": len(page_data["chunks"]),
            "heading": f"Page {page_num}",
        })

    # Sort by score (relevance) and return top-k pages
    return sorted(pages, key=lambda p: p["score"], reverse=True)[:top_k]


def main() -> int:
    parser = argparse.ArgumentParser(description="Test retriever for one uploaded document")
    parser.add_argument("--query", required=True, help="Question to test retrieval with")
    parser.add_argument("--doc-id", default=None, help="Document ID from database")
    parser.add_argument("--filename", default=None, help="Original or stored filename")
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks/pages to return")
    parser.add_argument(
        "--mode",
        default="chunk",
        choices=["chunk", "page"],
        help="Retrieval mode: chunk (fragmented) or page (full pages)",
    )
    parser.add_argument(
        "--source-type",
        default="uploaded",
        choices=["uploaded", "official_site"],
        help="Optional source filter",
    )
    args = parser.parse_args()

    try:
        resolved_doc_id = _resolve_doc_id(args.doc_id, args.filename)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 2

    print(f"\n[INFO] Query: {args.query}")
    print(f"[INFO] Mode: {args.mode} ({'full pages' if args.mode == 'page' else 'individual chunks'})")
    print(f"[INFO] Document ID: {resolved_doc_id}")

    if args.mode == "page":
        results = _retrieve_pages(
            query=args.query,
            doc_id=resolved_doc_id,
            source_type=args.source_type,
            top_k=args.top_k,
        )
    else:
        results = retrieve_context(
            query=args.query,
            top_k=args.top_k,
            source_type=args.source_type,
            doc_id=resolved_doc_id,
        )

    print(f"[INFO] Results returned: {len(results)}\n")

    if not results:
        print("[WARN] No results matched. Try removing source filter or using a broader query.")
        return 0

    if args.mode == "page":
        _print_pages(results)
    else:
        _print_chunks(results)

    return 0


def _print_chunks(chunks: list[dict]) -> None:
    """Print chunk-based results."""
    for idx, c in enumerate(chunks, 1):
        heading = c.get("heading") or "(no heading)"
        score = c.get("score", 0.0)
        method = c.get("retrieval_method", "unknown")
        text = str(c.get("text", "")).replace("\n", " ")
        preview = (text[:180] + "...") if len(text) > 180 else text

        print(f"[{idx}] score={score:.4f} method={method}")
        print(f"    heading={heading}")
        print(f"    preview={preview}\n")


def _print_pages(pages: list[dict]) -> None:
    """Print page-based results with full readable text."""
    for idx, p in enumerate(pages, 1):
        score = p.get("score", 0.0)
        page_num = p.get("page", 0)
        text = str(p.get("text", "")).strip()
        chunk_count = p.get("chunk_count", 0)

        print(f"{'='*80}")
        print(f"[PAGE {idx}] Page {page_num} | score={score:.4f} | chunks={chunk_count}")
        print(f"{'='*80}")
        print(f"\n{text}\n")
        print(f"{'='*80}\n")

if __name__ == "__main__":
    raise SystemExit(main())

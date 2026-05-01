"""
IMS AstroBot — Hybrid Chunker
Combines structural (heading-aware) splitting with fixed-size overlap chunking.
"""

import re
from tests.config import CHUNK_SIZE, CHUNK_OVERLAP


def _split_by_headings(text: str) -> list[dict]:
    """
    Split text into sections based on markdown-style headings.
    Returns a list of {"heading": str, "content": str} dicts.
    """
    # Pattern matches markdown headings (##, ###) or [Page X], [Slide X], [Sheet: X]
    heading_pattern = re.compile(
        r"^(#{1,6}\s+.+|"              # Markdown headings
        r"\[Page\s+\d+\]|"             # PDF page markers
        r"\[Slide\s+\d+\]|"            # PPTX slide markers
        r"##\s+Sheet:\s+.+)$",         # Excel sheet markers
        re.MULTILINE
    )

    sections = []
    matches = list(heading_pattern.finditer(text))

    if not matches:
        # No structure found — treat as single block
        return [{"heading": "", "content": text, "page_index": None, "section_type": "plain"}]

    # Content before first heading
    if matches[0].start() > 0:
        pre_content = text[:matches[0].start()].strip()
        if pre_content:
            sections.append({"heading": "", "content": pre_content, "page_index": None, "section_type": "plain"})

    # Split by headings
    for i, match in enumerate(matches):
        heading = match.group().strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            clean_heading, page_index, section_type = _normalize_heading_metadata(heading)
            sections.append(
                {
                    "heading": clean_heading,
                    "content": content,
                    "page_index": page_index,
                    "section_type": section_type,
                }
            )

    return sections


def _normalize_heading_metadata(heading: str) -> tuple[str, int | None, str]:
    """Normalize a structural heading and extract page-aware metadata when present."""
    cleaned = (heading or "").lstrip("#").strip()
    if not cleaned:
        return "", None, "plain"

    page_match = re.match(r"^\[(Page|Slide)\s+(\d+)\]$", cleaned, flags=re.IGNORECASE)
    if page_match:
        section_kind = page_match.group(1).lower()
        page_index = int(page_match.group(2))
        return f"{section_kind.title()} {page_index}", page_index, section_kind

    if cleaned.lower().startswith("sheet:"):
        return cleaned, None, "sheet"

    return cleaned, None, "heading"


def _fixed_size_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into fixed-size character chunks with overlap.
    Tries to break at sentence boundaries when possible.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            # Try to break at sentence boundary (. ! ? \n)
            boundary = -1
            search_zone = text[max(start + chunk_size // 2, start):end]
            for sep in [". ", ".\n", "! ", "? ", "\n\n", "\n"]:
                idx = search_zone.rfind(sep)
                if idx != -1:
                    boundary = max(start + chunk_size // 2, start) + idx + len(sep)
                    break

            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move forward with overlap
        start = end - overlap if end < len(text) else end

    return chunks


def chunk_document(
    text: str,
    source_name: str = "",
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    source_type: str = "uploaded",
    source_url: str | None = None,
    source_domain: str | None = None,
    page_title: str | None = None,
    department: str | None = None,
    document_type: str | None = None,
) -> list[dict]:
    """
    Hybrid chunking: first split by structure (headings), then apply fixed-size chunking.
    
    Returns list of dicts:
        {"text": str, "metadata": {"source": str, "heading": str, "chunk_index": int, ...}}
    """
    if not text or not text.strip():
        return []

    sections = _split_by_headings(text)
    all_chunks = []
    chunk_index = 0

    for section in sections:
        heading = section["heading"]
        content = section["content"]
        page_index = section.get("page_index")
        section_type = section.get("section_type", "heading")

        # Prepend heading to content for context
        if heading:
            content_with_heading = f"{heading}\n{content}"
        else:
            content_with_heading = content

        sub_chunks = _fixed_size_chunks(content_with_heading, chunk_size, overlap)

        for sub_chunk in sub_chunks:
            metadata = {
                "source": source_name,
                "heading": heading,
                "chunk_index": chunk_index,
                "source_type": source_type or "uploaded",
                "section_type": section_type,
            }
            if page_index is not None:
                metadata["page_index"] = page_index
            if source_url:
                metadata["source_url"] = source_url
            if source_domain:
                metadata["source_domain"] = source_domain
            if page_title:
                metadata["page_title"] = page_title
            if department:
                metadata["department"] = department
            if document_type:
                metadata["document_type"] = document_type

            all_chunks.append({
                "text": sub_chunk,
                "metadata": metadata,
            })
            chunk_index += 1

    return all_chunks

"""
IMS AstroBot — Hybrid Chunker
Combines structural (heading-aware) splitting with fixed-size overlap chunking.
"""

import re
from typing import Optional
from config import CHUNK_SIZE, CHUNK_OVERLAP


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
        return [{"heading": "", "content": text}]

    # Content before first heading
    if matches[0].start() > 0:
        pre_content = text[:matches[0].start()].strip()
        if pre_content:
            sections.append({"heading": "", "content": pre_content})

    # Split by headings
    for i, match in enumerate(matches):
        heading = match.group().strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            sections.append({"heading": heading, "content": content})

    return sections


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
    source_url: str = "",
    source_domain: str = "",
    page_title: str = "",
    extra_metadata: Optional[dict] = None,
) -> list[dict]:
    """
    Hybrid chunking: first split by structure (headings), then apply fixed-size chunking.
    
    Returns list of dicts:
        {"text": str, "metadata": {"source": str, "heading": str, "chunk_index": int}}
    """
    if not text or not text.strip():
        return []

    sections = _split_by_headings(text)
    all_chunks = []
    chunk_index = 0

    for section in sections:
        heading = section["heading"]
        content = section["content"]

        # Prepend heading to content for context
        if heading:
            content_with_heading = f"{heading}\n{content}"
        else:
            content_with_heading = content

        sub_chunks = _fixed_size_chunks(content_with_heading, chunk_size, overlap)

        for sub_chunk in sub_chunks:
            all_chunks.append({
                "text": sub_chunk,
                "metadata": {
                    "source": source_name,
                    "heading": heading.lstrip("#").strip() if heading else "",
                    "chunk_index": chunk_index,
                    "source_type": source_type,
                    "source_url": source_url,
                    "source_domain": source_domain,
                    "page_title": page_title,
                    **(extra_metadata or {}),
                },
            })
            chunk_index += 1

    return all_chunks

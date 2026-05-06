"""
IMS AstroBot — Hybrid Chunker
Combines structural (heading-aware) splitting with fixed-size overlap chunking.

Fixes applied:
  1. Heading no longer prepended to every sub-chunk — stored in metadata only,
     injected at retrieval time to avoid embedding bloat.
  2. Minimum chunk size guard prevents near-empty tail chunks from bad overlap math.
  3. Redundant max() in search_zone start calculation removed.
  4. Token-aware chunking via tiktoken (falls back to character count if unavailable).
  5. Heading regex and _normalize_heading_metadata now consistently handle the
     "Sheet:" prefix — regex captures raw sheet headings without ## so the
     downstream startswith check always sees the same format.
  6. Back-to-back headings with no content are skipped rather than stored as empty chunks.
"""

import re

try:
    import tiktoken
    _TOKENIZER = tiktoken.get_encoding("cl100k_base")  # works for GPT-4 / Ada-002
    _USE_TOKENS = True
except ImportError:  # tiktoken not installed — graceful character-count fallback
    _TOKENIZER = None
    _USE_TOKENS = False

from tests.config import CHUNK_SIZE, CHUNK_OVERLAP

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _len(text: str) -> int:
    """Return token count when tiktoken is available, else character count."""
    if _USE_TOKENS and _TOKENIZER:
        return len(_TOKENIZER.encode(text))
    return len(text)


def _split_by_headings(text: str) -> list[dict]:
    """
    Split text into sections based on markdown-style headings.

    Pattern covers:
      • Markdown headings  (# … ######)
      • PDF page markers   [Page N]
      • PPTX slide markers [Slide N]
      • Excel sheet markers [Sheet: <name>]   ← captured WITHOUT leading ##
                                                so _normalize_heading_metadata
                                                sees a consistent format.

    Returns a list of {"heading": str, "content": str,
                        "page_index": int|None, "section_type": str} dicts.
    """
    heading_pattern = re.compile(
        r"^("
        r"#{1,6}\s+.+|"             # Markdown headings
        r"\[Page\s+\d+\]|"          # PDF page markers
        r"\[Slide\s+\d+\]|"         # PPTX slide markers
        r"\[Sheet:\s+[^\]]+\]"       # Excel sheet markers  (Fix 5: no leading ##)
        r")$",
        re.MULTILINE,
    )

    matches = list(heading_pattern.finditer(text))

    if not matches:
        return [{"heading": "", "content": text.strip(),
                 "page_index": None, "section_type": "plain"}]

    sections: list[dict] = []

    # Content before first heading
    pre_content = text[: matches[0].start()].strip()
    if pre_content:
        sections.append({"heading": "", "content": pre_content,
                          "page_index": None, "section_type": "plain"})

    for i, match in enumerate(matches):
        heading = match.group().strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()

        # Fix 6: skip headings that have no associated content
        if not content:
            continue

        clean_heading, page_index, section_type = _normalize_heading_metadata(heading)
        sections.append(
            {
                "heading": clean_heading,
                "content": content,          # Fix 1: heading NOT prepended here
                "page_index": page_index,
                "section_type": section_type,
            }
        )

    return sections


def _normalize_heading_metadata(heading: str) -> tuple[str, int | None, str]:
    """Normalize a structural heading and extract page-aware metadata."""
    cleaned = (heading or "").lstrip("#").strip()
    if not cleaned:
        return "", None, "plain"

    # [Page N] / [Slide N]
    page_match = re.match(r"^\[(Page|Slide)\s+(\d+)\]$", cleaned, flags=re.IGNORECASE)
    if page_match:
        section_kind = page_match.group(1).lower()
        page_index = int(page_match.group(2))
        return f"{section_kind.title()} {page_index}", page_index, section_kind

    # [Sheet: <name>]  (Fix 5: match bracket form directly)
    sheet_match = re.match(r"^\[Sheet:\s*(.+)\]$", cleaned, flags=re.IGNORECASE)
    if sheet_match:
        return f"Sheet: {sheet_match.group(1).strip()}", None, "sheet"

    return cleaned, None, "heading"


def _fixed_size_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    min_chunk_size: int = 50,          # Fix 2: minimum chunk guard (tokens or chars)
) -> list[str]:
    """
    Split text into fixed-size chunks with overlap.

    • Size is measured in tokens when tiktoken is available, else characters.
    • Tries to break at sentence boundaries to preserve readability.
    • Chunks smaller than min_chunk_size are discarded (avoids overlap artifacts).
    """
    if _len(text) <= chunk_size:
        return [text]

    # Work in character space for slicing; token lengths guide boundaries.
    chunks: list[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        # Extend end until the slice reaches chunk_size tokens/chars
        end = start
        while end < text_len and _len(text[start:end]) < chunk_size:
            end = min(end + max(chunk_size, 1), text_len)

        if end < text_len:
            # Fix 3: search zone start is simply start + half the slice length
            half = (end - start) // 2
            search_start = start + half
            search_zone = text[search_start:end]

            boundary = -1
            for sep in (". ", ".\n", "! ", "? ", "\n\n", "\n"):
                idx = search_zone.rfind(sep)
                if idx != -1:
                    boundary = search_start + idx + len(sep)
                    break

            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()

        # Fix 2: discard near-empty tail chunks produced by overlap math
        if chunk and _len(chunk) >= min_chunk_size:
            chunks.append(chunk)

        if end >= text_len:
            break

        # Overlap: step back by `overlap` tokens/chars
        if _USE_TOKENS and _TOKENIZER:
            tokens = _TOKENIZER.encode(text[start:end])
            overlap_tokens = tokens[-overlap:] if overlap < len(tokens) else tokens
            overlap_text = _TOKENIZER.decode(overlap_tokens)
            start = end - len(overlap_text)
        else:
            start = end - overlap

        # Safety: always advance to prevent infinite loop
        if start <= (end - (end - start)):
            start = end

    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

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
    Hybrid chunking: split by structure (headings) → fixed-size chunks per section.

    The section heading is stored **only in metadata** (not prepended to chunk text)
    so embeddings reflect the actual content rather than repeated heading strings.
    Consumers that want heading context can prepend ``metadata["heading"]`` at
    retrieval time.

    Returns::

        [
            {
                "text": str,
                "metadata": {
                    "source": str,
                    "heading": str,
                    "chunk_index": int,
                    "source_type": str,
                    "section_type": str,
                    # optional: page_index, source_url, source_domain,
                    #           page_title, department, document_type
                }
            },
            ...
        ]
    """
    if not text or not text.strip():
        return []

    sections = _split_by_headings(text)
    all_chunks: list[dict] = []
    chunk_index = 0

    for section in sections:
        heading = section["heading"]
        content = section["content"]
        page_index = section.get("page_index")
        section_type = section.get("section_type", "heading")

        # Fix 1: content is chunked as-is; heading lives only in metadata
        sub_chunks = _fixed_size_chunks(content, chunk_size, overlap)

        for sub_chunk in sub_chunks:
            metadata: dict = {
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

            all_chunks.append({"text": sub_chunk, "metadata": metadata})
            chunk_index += 1

    return all_chunks
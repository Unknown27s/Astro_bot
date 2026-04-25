"""
IMS AstroBot — Upload-driven Question Suggester

Generates practical, user-facing question suggestions from uploaded
document content (chunks + metadata) for display in the chat UI.

Public API (used by other modules):
    generate_document_questions(filename, text, chunks, limit) -> list[str]
    generate_multi_document_questions(documents, limit)        -> list[str]
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration — all tuneable values in one place
# ---------------------------------------------------------------------------

# Maximum headings / keywords harvested before question generation
_MAX_HEADINGS: int = 10
_MAX_KEYWORDS: int = 10

# Minimum character length for a heading to be considered meaningful
_MIN_HEADING_LENGTH: int = 4

# Topic patterns ordered by institutional relevance.
# Each tuple is (pattern, human-readable label used in the question).
_TOPIC_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\b(admission|eligibility|application|selection|enrolment)\b", "admission"),
    (r"\b(fee|tuition|payment|refund|scholarship|stipend)\b",        "fee"),
    (r"\b(attendance|absence|leave|shortage|late)\b",                "attendance"),
    (r"\b(exam|assessment|internal|mark|grade|result|cgpa)\b",       "exam"),
    (r"\b(hostel|transport|canteen|library|placement|internship)\b",  "facilities"),
    (r"\b(policy|rule|regulation|procedure|guideline|conduct)\b",     "rules"),
    (r"\b(deadline|last date|schedule|calendar|timetable)\b",        "deadlines"),
    (r"\b(course|programme|curriculum|syllabus|subject|credit)\b",   "courses"),
    (r"\b(disciplinary|misconduct|suspension|grievance|appeal)\b",   "disciplinary"),
    (r"\b(certificate|degree|transcript|provisional|convocation)\b", "certificates"),
)


# ---------------------------------------------------------------------------
# Internal types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _DocSignals:
    """Signals extracted from a single document — feeds question generation."""
    doc_label: str           # human-readable name shown in questions
    headings:  list[str] = field(default_factory=list)
    topics:    list[str] = field(default_factory=list)   # human labels, not raw tokens


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _clean_filename(filename: str) -> str:
    """Turn a filename into a readable label, e.g. 'fee_policy_2024.pdf' → 'fee policy 2024'."""
    stem = Path(filename or "document").stem
    label = re.sub(r"[_\-]+", " ", stem).strip()
    return label or "this document"


def _normalize_heading(raw: str) -> str:
    cleaned = re.sub(r"\s+", " ", (raw or "").strip())
    cleaned = cleaned.strip("#-:| \t")
    return cleaned


def _extract_headings(chunks: list[dict], max_items: int = _MAX_HEADINGS) -> list[str]:
    """
    Pull unique, non-trivial headings from chunk metadata.
    Accepts both flat dicts (heading at top level) and dicts with a
    nested 'metadata' key — handles both ingestion shapes.
    """
    headings: list[str] = []
    seen: set[str] = set()

    for chunk in chunks or []:
        if not isinstance(chunk, dict):
            continue

        # Support both metadata-nested and flat chunk shapes
        meta = chunk.get("metadata") or chunk
        raw = meta.get("heading") or meta.get("page_title") or ""
        heading = _normalize_heading(raw)

        if len(heading) < _MIN_HEADING_LENGTH:
            continue

        key = heading.lower()
        if key in seen:
            continue

        seen.add(key)
        headings.append(heading)

        if len(headings) >= max_items:
            break

    return headings


def _extract_topics(text: str, max_items: int = _MAX_KEYWORDS) -> list[str]:
    """
    Scan document text for institutional topic signals and return
    their human-readable labels (deduplicated, order-preserving).
    """
    text_l = (text or "").lower()
    found: list[str] = []
    seen: set[str] = set()

    for pattern, label in _TOPIC_PATTERNS:
        if label in seen:
            continue
        if re.search(pattern, text_l):
            seen.add(label)
            found.append(label)
            if len(found) >= max_items:
                break

    return found


def _deduplicate(questions: list[str], limit: int) -> list[str]:
    """Return up to `limit` questions with exact-lowercase deduplication."""
    unique: list[str] = []
    seen: set[str] = set()

    for raw in questions:
        q = re.sub(r"\s+", " ", raw).strip()
        if not q:
            continue
        key = q.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(q)
        if len(unique) >= limit:
            break

    return unique


# ---------------------------------------------------------------------------
# Signal extraction
# ---------------------------------------------------------------------------

def _extract_signals(filename: str, text: str, chunks: list[dict]) -> _DocSignals:
    return _DocSignals(
        doc_label=_clean_filename(filename),
        headings=_extract_headings(chunks),
        topics=_extract_topics(text),
    )


# ---------------------------------------------------------------------------
# Question builders  (each returns a list in priority order)
# ---------------------------------------------------------------------------

def _base_questions(doc_label: str) -> list[str]:
    """Generic questions that apply to any document."""
    return [
        f"Can you summarise the key points from {doc_label}?",
        f"What are the most important rules or policies in {doc_label}?",
        f"What should a student know before reading {doc_label}?",
    ]


def _heading_questions(doc_label: str, headings: list[str]) -> list[str]:
    return [f"What does the section '{h}' cover in {doc_label}?" for h in headings]


def _topic_questions(doc_label: str, topics: list[str]) -> list[str]:
    # Map topic labels to natural question phrasing
    _TOPIC_QUESTIONS: dict[str, str] = {
        "admission":      "What are the admission or eligibility requirements in {doc}?",
        "fee":            "What does {doc} say about fees, payments, or refunds?",
        "attendance":     "What is the attendance policy described in {doc}?",
        "exam":           "How are exams and assessments handled according to {doc}?",
        "facilities":     "What facilities or services are mentioned in {doc}?",
        "rules":          "What conduct rules or regulations does {doc} cover?",
        "deadlines":      "Are there important deadlines or schedules in {doc}?",
        "courses":        "What courses or programmes are described in {doc}?",
        "disciplinary":   "What are the disciplinary procedures outlined in {doc}?",
        "certificates":   "How can students obtain certificates or transcripts per {doc}?",
    }

    questions: list[str] = []
    for topic in topics:
        template = _TOPIC_QUESTIONS.get(topic)
        if template:
            questions.append(template.format(doc=doc_label))
        else:
            questions.append(f"What does {doc_label} say about {topic}?")
    return questions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_document_questions(
    filename: str,
    text: str,
    chunks: list[dict],
    limit: int = 10,
) -> list[str]:
    """
    Generate user-facing question suggestions for a single uploaded document.

    Args:
        filename: Original filename (used to build a readable label).
        text:     Full extracted text of the document.
        chunks:   Chunk dicts from the ingestion pipeline.
                  Accepts both flat chunks and chunks with a nested 'metadata' key.
        limit:    Maximum number of questions to return.

    Returns:
        Deduplicated list of question strings, up to `limit` items.
    """
    if not (text or "").strip() and not chunks:
        return []

    signals = _extract_signals(filename, text, chunks)

    # Build questions in priority order:
    # base → topic (high-value) → heading (structural detail)
    all_questions = (
        _base_questions(signals.doc_label)
        + _topic_questions(signals.doc_label, signals.topics)
        + _heading_questions(signals.doc_label, signals.headings)
    )

    return _deduplicate(all_questions, limit)


def generate_multi_document_questions(
    documents: list[dict],
    limit: int = 12,
) -> list[str]:
    """
    Generate question suggestions across multiple uploaded documents.

    Useful when the user has uploaded several files and the UI wants a
    combined set of suggested questions.

    Args:
        documents: List of dicts, each with keys:
                       filename (str)
                       text     (str)
                       chunks   (list[dict])
        limit:     Maximum total questions to return.

    Returns:
        Interleaved, deduplicated questions from all documents.
    """
    if not documents:
        return []

    per_doc_limit = max(3, limit // max(len(documents), 1))
    all_questions: list[str] = []

    for doc in documents:
        if not isinstance(doc, dict):
            continue
        questions = generate_document_questions(
            filename=doc.get("filename", "document"),
            text=doc.get("text", ""),
            chunks=doc.get("chunks", []),
            limit=per_doc_limit,
        )
        all_questions.extend(questions)

    return _deduplicate(all_questions, limit)
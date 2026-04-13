"""
IMS AstroBot — Upload-driven Question Suggester
Creates practical suggested questions from uploaded document content.
"""

from __future__ import annotations

import re
from pathlib import Path


def _normalize_heading(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    cleaned = cleaned.strip("#-: ")
    return cleaned


def _extract_headings(chunks: list[dict], max_items: int = 8) -> list[str]:
    headings = []
    seen = set()
    for chunk in chunks or []:
        metadata = chunk.get("metadata", {}) if isinstance(chunk, dict) else {}
        heading = _normalize_heading(metadata.get("heading", ""))
        if not heading:
            continue
        key = heading.lower()
        if key in seen:
            continue
        seen.add(key)
        headings.append(heading)
        if len(headings) >= max_items:
            break
    return headings


def _extract_topic_keywords(text: str, max_items: int = 8) -> list[str]:
    topic_patterns = [
        r"\b(admission|eligibility|application|selection)\b",
        r"\b(fee|tuition|payment|refund|scholarship)\b",
        r"\b(attendance|absence|leave|shortage)\b",
        r"\b(exam|assessment|internal|mark|grade|result)\b",
        r"\b(hostel|transport|canteen|library|placement)\b",
        r"\b(policy|rule|regulation|procedure|guideline)\b",
        r"\b(deadline|last date|schedule|calendar|timetable)\b",
    ]

    text_l = (text or "").lower()
    found = []
    seen = set()
    for pattern in topic_patterns:
        match = re.search(pattern, text_l)
        if not match:
            continue
        token = match.group(1)
        if token in seen:
            continue
        seen.add(token)
        found.append(token)
        if len(found) >= max_items:
            break
    return found


def generate_document_questions(filename: str, text: str, chunks: list[dict], limit: int = 10) -> list[str]:
    """Generate high-value, user-facing question suggestions from one uploaded document."""
    if not text or not text.strip():
        return []

    doc_name = Path(filename or "document").stem.replace("_", " ").strip() or "this document"
    headings = _extract_headings(chunks, max_items=8)
    keywords = _extract_topic_keywords(text, max_items=8)

    questions = [
        f"Can you summarize key points from {doc_name}?",
        f"What are the most important rules in {doc_name}?",
    ]

    for heading in headings:
        questions.append(f"What does the section '{heading}' explain?")

    for keyword in keywords:
        questions.append(f"What does {doc_name} say about {keyword}?")

    # Keep unique questions while preserving order.
    unique = []
    seen = set()
    for q in questions:
        question = re.sub(r"\s+", " ", q).strip()
        if not question:
            continue
        key = question.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(question)
        if len(unique) >= limit:
            break

    return unique

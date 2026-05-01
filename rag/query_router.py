"""
IMS AstroBot — Query Router

Classifies chat queries into one of six routes:
  official_site | document | faq | hybrid | general_chat | unclear
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import NamedTuple


class StrEnum(str, Enum):
    """Python 3.10-compatible replacement for enum.StrEnum."""
    pass

from tests.config import ENABLE_GENERAL_CHAT_ROUTING


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class Route(StrEnum):
    OFFICIAL_SITE = "official_site"
    DOCUMENT      = "document"
    TIMETABLE     = "timetable"
    FAQ           = "faq"
    HYBRID        = "hybrid"
    GENERAL_CHAT  = "general_chat"
    UNCLEAR       = "unclear"


class MemoryScope(StrEnum):
    OFFICIAL_SITE = "official_site"
    DOCUMENT      = "document"
    GENERAL_CHAT  = "general_chat"


@dataclass(frozen=True)
class QueryRoute:
    mode: Route
    confidence: float
    reason: str
    source_type: str | None = None
    memory_scope: MemoryScope | None = None
    filters: dict | None = None
    complexity_score: int = 1


# ---------------------------------------------------------------------------
# Signal configuration
# ---------------------------------------------------------------------------

class _SignalGroup(NamedTuple):
    """A named collection of keyword signals with a base confidence."""
    name: str
    keywords: frozenset[str]
    base_confidence: float = 0.60
    confidence_per_hit: float = 0.10
    max_confidence: float = 0.95

    def score(self, text: str) -> tuple[int, list[str]]:
        hits = []
        for kw in self.keywords:
            if " " in kw:
                # Keep phrase matching for multi-word signals.
                if kw in text:
                    hits.append(kw)
            else:
                # Single-word signals use boundaries to avoid false positives (e.g., "hi" in "scholarship").
                if re.search(rf"\b{re.escape(kw)}\b", text):
                    hits.append(kw)
        return len(hits), hits

    def confidence(self, hits: int) -> float:
        return round(
            min(self.max_confidence, self.base_confidence + hits * self.confidence_per_hit),
            2,
        )


_OFFICIAL_SITE = _SignalGroup(
    name="official_site",
    keywords=frozenset({
        "how is this college", "about this college",
        "college", "campus", "course", "courses",
        "fee", "fees", "admission", "admissions",
        "department", "departments", "placement", "placements",
        "hostel", "library", "facility", "facilities",
        "contact", "address", "website", "overview",
    }),
)

_DOCUMENT = _SignalGroup(
    name="document",
    keywords=frozenset({
        "policy", "policies", "handbook", "notice", "circular",
        "regulation", "regulations", "syllabus", 
        "exam", "attendance", "leave", "rules",
        "document", "documents", "pdf", "file", "uploaded",
        "technical", "code", "api", "config", "database",
        "rag", "chromadb", "fastapi", "spring boot",
    }),
)

_TIMETABLE = _SignalGroup(
    name="timetable",
    keywords=frozenset({
        "timetable", "schedule", "class room", "room", "present",
        "what class", "which class", "period"
    }),
)

_FAQ = _SignalGroup(
    name="faq",
    keywords=frozenset({
        "what is", "how to", "how do i", "when is", "where is",
        "eligibility", "deadline", "last date",
        "application process", "fee structure",
        "scholarship", "required documents",
    }),
    base_confidence=0.62,
    confidence_per_hit=0.08,
)

_FAQ_SPECIFIC = _SignalGroup(
    name="faq_specific",
    keywords=frozenset({
        "eligibility", "deadline", "last date",
        "application process", "fee structure",
        "scholarship", "required documents",
    }),
)

_GENERAL_CHAT = _SignalGroup(
    name="general_chat",
    keywords=frozenset({
        "hello", "hi", "hey", "how are you",
        "good morning", "good evening",
        "tell me a joke", "who are you",
        "thank you", "thanks",
    }),
)


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

def _normalize(query: str) -> str:
    return " ".join(query.lower().split())


def _faq_source(official_hits: int, document_hits: int) -> tuple[str, MemoryScope]:
    if official_hits >= document_hits:
        return "official_site", MemoryScope.OFFICIAL_SITE
    return "uploaded", MemoryScope.DOCUMENT


def _resolve(
    *,
    text: str,
    official: tuple[int, list[str]],
    document: tuple[int, list[str]],
    timetable: tuple[int, list[str]],
    faq:      tuple[int, list[str]],
    faq_specific: tuple[int, list[str]],
    general:  tuple[int, list[str]],
) -> QueryRoute:
    official_n, official_hits = official
    document_n, document_hits = document
    timetable_n, timetable_hits = timetable
    faq_n,      faq_hits      = faq
    faq_specific_n, _         = faq_specific
    general_n,  general_hits  = general

    # Timetable explicitly overrides other routes if it has high confidence
    if timetable_n > 0:
        return QueryRoute(
            mode=Route.TIMETABLE,
            confidence=_TIMETABLE.confidence(timetable_n),
            reason=f"timetable/schedule signals: {', '.join(timetable_hits[:4])}",
            source_type="database",
        )

    has_institutional = bool(official_n or document_n or faq_specific_n)

    # General chat — only when there's no institutional context
    if ENABLE_GENERAL_CHAT_ROUTING and general_n and not has_institutional:
        return QueryRoute(
            mode=Route.GENERAL_CHAT,
            confidence=_GENERAL_CHAT.confidence(general_n),
            reason=f"general chat signals: {', '.join(general_hits[:4])}",
            memory_scope=MemoryScope.GENERAL_CHAT,
        )

    # FAQ with institutional backing
    if faq_n and has_institutional:
        source_type, memory_scope = _faq_source(official_n, document_n)
        all_hits = (faq_hits + official_hits + document_hits)[:4]
        return QueryRoute(
            mode=Route.FAQ,
            confidence=_FAQ.confidence(faq_n),
            reason=f"faq intent with institutional signals: {', '.join(all_hits)}",
            source_type=source_type,
            memory_scope=memory_scope,
        )

    # Both official and document signals present
    if official_n and document_n:
        dominant = official_n if official_n > document_n else document_n
        gap = abs(official_n - document_n)
        confidence = _OFFICIAL_SITE.confidence(dominant)

        if gap <= 1:
            return QueryRoute(
                mode=Route.HYBRID,
                confidence=confidence,
                reason=f"mixed campus and document signals: {', '.join((official_hits + document_hits)[:4])}",
            )
        if official_n > document_n:
            return QueryRoute(
                mode=Route.OFFICIAL_SITE,
                confidence=confidence,
                reason=f"public campus signals: {', '.join(official_hits[:4])}",
                source_type="official_site",
                memory_scope=MemoryScope.OFFICIAL_SITE,
            )
        return QueryRoute(
            mode=Route.DOCUMENT,
            confidence=confidence,
            reason=f"document-specific signals: {', '.join(document_hits[:4])}",
            source_type="uploaded",
            memory_scope=MemoryScope.DOCUMENT,
        )

    if official_n:
        return QueryRoute(
            mode=Route.OFFICIAL_SITE,
            confidence=_OFFICIAL_SITE.confidence(official_n),
            reason=f"public campus signals: {', '.join(official_hits[:4])}",
            source_type="official_site",
            memory_scope=MemoryScope.OFFICIAL_SITE,
        )

    if document_n:
        return QueryRoute(
            mode=Route.DOCUMENT,
            confidence=_DOCUMENT.confidence(document_n),
            reason=f"document-specific signals: {', '.join(document_hits[:4])}",
            source_type="uploaded",
            memory_scope=MemoryScope.DOCUMENT,
        )

    return QueryRoute(mode=Route.UNCLEAR, confidence=0.2, reason="no clear routing signals")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _extract_query_metadata(text: str) -> tuple[dict, int]:
    """Extract expected department/document_type filters and complexity score."""
    filters = {}
    
    # Department rules
    if "library" in text:
        filters["department"] = "library"
    elif "admission" in text:
        filters["department"] = "admissions"
    elif "placement" in text:
        filters["department"] = "placements"
    elif "hostel" in text:
        filters["department"] = "hostel"

    # Document type rules
    if "policy" in text or "rules" in text:
        filters["document_type"] = "policy"
    elif "syllabus" in text:
        filters["document_type"] = "syllabus"
    elif "schedule" in text or "calendar" in text or "timetable" in text:
        filters["document_type"] = "schedule"
        
    # Complexity rules
    words = text.split()
    complexity_score = 1
    if len(words) > 12 or any(w in text for w in ["explain", "describe", "detail", "process", "difference"]):
        complexity_score = 3
    elif len(words) > 6 or any(w in text for w in ["how", "why"]):
        complexity_score = 2

    return filters, complexity_score


def classify_query_route(query: str) -> QueryRoute:
    if not (text := _normalize(query)):
        return QueryRoute(mode=Route.UNCLEAR, confidence=0.0, reason="empty query")

    route = _resolve(
        text=text,
        official=_OFFICIAL_SITE.score(text),
        document=_DOCUMENT.score(text),
        timetable=_TIMETABLE.score(text),
        faq=_FAQ.score(text),
        faq_specific=_FAQ_SPECIFIC.score(text),
        general=_GENERAL_CHAT.score(text),
    )
    
    filters, complexity = _extract_query_metadata(text)
    
    # Use object.__setattr__ because the dataclass is frozen
    if filters:
        object.__setattr__(route, 'filters', filters)
    object.__setattr__(route, 'complexity_score', complexity)
    
    return route
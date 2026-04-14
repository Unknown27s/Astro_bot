"""
IMS AstroBot — Query Router
Classifies chat queries into official-site, document, hybrid, or unclear routes.
"""

from dataclasses import dataclass


_OFFICIAL_SITE_PHRASES = (
    "how is this college",
    "about this college",
    "college",
    "campus",
    "course",
    "courses",
    "fee",
    "fees",
    "admission",
    "admissions",
    "department",
    "departments",
    "placement",
    "placements",
    "hostel",
    "library",
    "facility",
    "facilities",
    "contact",
    "address",
    "website",
    "overview",
)

_DOCUMENT_PHRASES = (
    "policy",
    "policies",
    "handbook",
    "notice",
    "circular",
    "regulation",
    "regulations",
    "syllabus",
    "timetable",
    "exam",
    "attendance",
    "leave",
    "rules",
    "document",
    "documents",
    "pdf",
    "file",
    "uploaded",
    "technical",
    "code",
    "api",
    "config",
    "database",
    "rag",
    "chromadb",
    "fastapi",
    "spring boot",
)


@dataclass(frozen=True)
class QueryRoute:
    mode: str
    confidence: float
    reason: str
    source_type: str | None = None
    memory_scope: str | None = None


def _normalize(query: str) -> str:
    return " ".join((query or "").lower().split())


def _score(query: str, phrases: tuple[str, ...]) -> tuple[int, list[str]]:
    score = 0
    hits: list[str] = []
    for phrase in phrases:
        if phrase in query:
            score += 1
            hits.append(phrase)
    return score, hits


def classify_query_route(query: str) -> QueryRoute:
    normalized = _normalize(query)
    if not normalized:
        return QueryRoute(mode="unclear", confidence=0.0, reason="empty query")

    official_score, official_hits = _score(normalized, _OFFICIAL_SITE_PHRASES)
    document_score, document_hits = _score(normalized, _DOCUMENT_PHRASES)

    if official_score and document_score:
        gap = abs(official_score - document_score)
        confidence = min(0.95, 0.55 + (max(official_score, document_score) * 0.1))
        if gap <= 1:
            return QueryRoute(
                mode="hybrid",
                confidence=round(confidence, 2),
                reason=f"mixed campus and document signals: {', '.join((official_hits + document_hits)[:4])}",
            )
        if official_score > document_score:
            return QueryRoute(
                mode="official_site",
                confidence=round(confidence, 2),
                reason=f"public campus signals: {', '.join(official_hits[:4])}",
                source_type="official_site",
                memory_scope="official_site",
            )
        return QueryRoute(
            mode="document",
            confidence=round(confidence, 2),
            reason=f"document-specific signals: {', '.join(document_hits[:4])}",
            source_type="uploaded",
            memory_scope="document",
        )

    if official_score:
        confidence = min(0.95, 0.60 + official_score * 0.1)
        return QueryRoute(
            mode="official_site",
            confidence=round(confidence, 2),
            reason=f"public campus signals: {', '.join(official_hits[:4])}",
            source_type="official_site",
            memory_scope="official_site",
        )

    if document_score:
        confidence = min(0.95, 0.60 + document_score * 0.1)
        return QueryRoute(
            mode="document",
            confidence=round(confidence, 2),
            reason=f"document-specific signals: {', '.join(document_hits[:4])}",
            source_type="uploaded",
            memory_scope="document",
        )

    return QueryRoute(
        mode="unclear",
        confidence=0.2,
        reason="no clear routing signals",
    )

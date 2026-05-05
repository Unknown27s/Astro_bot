"""
Fast heuristic tool router for AstroBot.

Replaces the previous LLM-based router that added 1-3s latency per query.
Uses keyword signals (consistent with query_router.py) to decide whether
a query needs the SQL agent.

Improvements over v1:
  - Word-boundary matching prevents false positives from substring collisions
    (e.g. "internal" no longer fires on "internal combustion engine").
  - Ambiguous single-word signals are separated into a WEAK tier that only
    fire when a second corroborating signal is also present.
  - Multi-word phrases are matched properly using substring search on the
    full normalised text (not word-boundary matching, since phrases span tokens).
  - Returns a confidence level ('high' / 'low' / 'none') so the caller can
    decide whether to try both paths on low-confidence hits.
"""

import re
import logging

logger = logging.getLogger(__name__)

# ── Strong signals: single words that almost exclusively mean DB lookup ──
# Matched with word boundaries (\b) to avoid substring collisions.
_STRONG_SINGLE = frozenset({
    "timetable", "schedule",
    "marks", "scores", "grades", "cgpa", "gpa",
    "results",          # plural is safer than "result" alone
    "topper", "toppers",
    "attendance",
    "semester",         # in college context almost always DB
    "marksheet",        # normalised form (no space)
})

# ── Weak signals: common words that can mean DB lookup but also appear in
#    general knowledge questions. Only trigger when TWO or more weak signals
#    are present, OR when one weak signal + one strong signal is present.
_WEAK_SINGLE = frozenset({
    "mark",             # "mark my words" — needs corroboration
    "score",            # "score in cricket" — needs corroboration
    "grade",            # "grade 12 physics" — needs corroboration
    "result",           # "result of the experiment" — needs corroboration
    "internal",         # "internal combustion" — needs corroboration
    "external",
    "pass", "fail",
    "subject",
    "class",            # "class in python" — needs corroboration
    "period",           # "period in chemistry" — needs corroboration
    "room",             # "room temperature" — needs corroboration
    "student",
    "exam", "exams",
    "test",
    "paper",
    "batch",
    "section",
    "department",
    "average",
    "percentage",
})

# ── Strong multi-word phrases: matched as substrings on normalised text ──
# These are specific enough that a single match is sufficient.
_STRONG_PHRASES = frozenset({
    "roll no", "roll number", "roll nos",
    "student id", "student ids",
    "subject code",
    "marks sheet", "mark sheet",
    "class room",           # spaced variant
    "next class", "my class",
    "what class", "which class",
    "who scored", "who got", "who topped",
    "highest marks", "lowest marks", "average marks",
    "my marks", "my score", "my grades", "my result", "my cgpa",
    "my gpa", "my attendance", "my timetable", "my schedule",
    "show marks", "show result", "check marks",
    "did i pass", "did i fail", "have i passed",
    "this semester", "last semester", "current semester",
    "first year", "second year", "third year", "fourth year",
    "internal marks", "external marks",
    "class schedule", "class timetable",
    "period on", "period for",
    "free period", "free class",
    "lab schedule", "lab timetable",
})

# ── Hard exclusion phrases: if any of these appear, always return 'none'
#    regardless of other signals. Prevents routing clearly general-knowledge
#    questions to the SQL agent.
_EXCLUSION_PHRASES = frozenset({
    "internal combustion",
    "grade 12", "grade 11", "grade 10",  # school-level academic queries
    "what is a", "what is an", "explain",
    "define ", "definition of",
    "how does", "how do",
    "why is", "why does", "why are",
    "tell me about",
    "what are the",
})


def _normalise(query: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation except spaces."""
    text = query.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)   # punctuation → space
    return re.sub(r"\s+", " ", text)        # collapse whitespace


def _has_word(text: str, word: str) -> bool:
    """True if `word` appears as a whole word in `text`."""
    return bool(re.search(r"\b" + re.escape(word) + r"\b", text))


def get_tool_for_query(query: str) -> dict:
    """
    Returns a routing decision dict:
        {
            "tool":       "sql_agent" | "none",
            "confidence": "high" | "low" | "none",
            "matched":    <keyword or phrase that triggered the decision>
        }

    Pure heuristic — runs in <1ms with zero LLM overhead.
    """
    text = _normalise(query)

    # ── 1. Hard exclusions — bail immediately ──
    for phrase in _EXCLUSION_PHRASES:
        if phrase in text:
            logger.info(f"Tool Router: none (excluded by '{phrase}')")
            return {"tool": "none", "confidence": "none", "matched": phrase}

    # ── 2. Strong multi-word phrases — high confidence ──
    for phrase in _STRONG_PHRASES:
        if phrase in text:
            logger.info(f"Tool Router: sql_agent HIGH (phrase: '{phrase}')")
            return {"tool": "sql_agent", "confidence": "high", "matched": phrase}

    # ── 3. Strong single words — high confidence ──
    for word in _STRONG_SINGLE:
        if _has_word(text, word):
            logger.info(f"Tool Router: sql_agent HIGH (word: '{word}')")
            return {"tool": "sql_agent", "confidence": "high", "matched": word}

    # ── 4. Weak single words — need corroboration ──
    weak_hits = [w for w in _WEAK_SINGLE if _has_word(text, w)]

    if len(weak_hits) >= 2:
        matched = ", ".join(weak_hits[:2])
        logger.info(f"Tool Router: sql_agent LOW (weak pair: '{matched}')")
        return {"tool": "sql_agent", "confidence": "low", "matched": matched}

    if weak_hits:
        logger.info(f"Tool Router: none (single weak signal: '{weak_hits[0]}')")

    return {"tool": "none", "confidence": "none", "matched": None}
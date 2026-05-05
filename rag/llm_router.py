"""
Fast heuristic tool router for AstroBot.

Replaces the previous LLM-based router that added 1-3s latency per query.
Uses keyword signals (consistent with query_router.py) to decide whether 
a query needs the SQL agent.
"""

import logging

logger = logging.getLogger(__name__)

# Keywords that strongly indicate a database query
_SQL_KEYWORDS = frozenset({
    "timetable", "schedule", "class room", "period",
    "what class", "which class", "next class",
    "mark", "marks", "score", "scores", "grade", "grades",
    "result", "results", "cgpa", "gpa", "semester",
    "internal", "external", "marks sheet",
    "roll no", "roll number", "student id",
    "subject code", "topper", "average marks",
    "who scored", "who got", "highest marks", "lowest marks",
})

def get_tool_for_query(query: str) -> str:
    """
    Returns 'sql_agent' if the query needs database lookup, else 'none'.
    Pure keyword-based — runs in <1ms with zero LLM overhead.
    """
    text = " ".join(query.lower().split())
    
    for keyword in _SQL_KEYWORDS:
        if keyword in text:
            logger.info(f"Tool Router: sql_agent (matched: '{keyword}')")
            return "sql_agent"
    
    return "none"

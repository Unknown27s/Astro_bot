"""
Unified Text-to-SQL Agent for AstroBot.

Instead of hardcoded parameter extraction, this agent lets the LLM
dynamically write SQL queries against the institute_data.db database.
It handles timetable, student info, and marks queries through a single
intelligent agent.

Flow:
  1. Inject the database schema into the LLM prompt.
  2. LLM writes a SELECT query based on the user's natural language question.
  3. Execute the query via a read-only connection (security enforced).
  4. Feed results back to LLM for a natural language answer.
  5. If SQL fails, retry once with the error message for self-correction.
"""

import json
import logging
from typing import Union, List, Dict
from rag.providers.manager import get_manager
from database.institute_db import get_schema_for_llm, execute_readonly_query

logger = logging.getLogger(__name__)

# ── System prompt for SQL generation ──
SQL_GENERATION_PROMPT = """You are an expert SQL query generator for an educational institute database.
You will be given the database schema and a user's question. Write a SQLite-compatible SELECT query to answer it.

RULES:
1. Output ONLY a valid JSON object: {{"sql": "YOUR SELECT QUERY HERE", "explanation": "brief reason"}}
2. Use ONLY SELECT statements. No INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
3. Use LIKE with % wildcards for flexible text matching (e.g., class_name LIKE '%CCE%').
4. Use case-insensitive matching: LOWER(column) LIKE LOWER('%value%').
5. For day-based queries, match partial day names (e.g., LOWER(day) LIKE '%mon%' for Monday).
6. When joining tables, use the foreign key: student_marks.student_id = students.id.
7. Always return useful columns — don't just SELECT *.
8. If the question is ambiguous, make a reasonable assumption and include it in the explanation.

DATABASE SCHEMA:
{schema}
"""

# ── System prompt for answer synthesis ──
SYNTHESIS_PROMPT = """You are an AI assistant for a college/institute. 
Based on the database query results below, answer the user's question clearly and helpfully.
If the results are empty, say so politely. Format tables using markdown when appropriate.
Be concise but thorough."""


def execute_sql_agent(query: str, trace=None, user_context: str | None = None) -> str:
    """
    Unified Text-to-SQL agent.
    
    Args:
        query: The user's natural language question.
        trace: Optional PipelineTrace for terminal transparency.
    
    Returns:
        A natural language response based on database results.
    """
    mgr = get_manager()
    schema = get_schema_for_llm()
    
    # ── Step 1: Ask LLM to generate SQL ──
    logger.info(f"SQL Agent: Generating query for: {query[:100]}")
    
    sql_prompt = SQL_GENERATION_PROMPT.format(schema=schema)

    user_message = f"User question: {query}"
    if user_context:
        user_message = f"STUDENT CONTEXT:\n{user_context}\n\n{user_message}"
    
    try:
        sql_response = mgr.generate(
            system_prompt=sql_prompt,
            user_message=user_message,
            temperature=0.0,
            max_tokens=300
        )
        
        if not sql_response:
            return "I couldn't generate a database query for your question. Could you rephrase it?"
        
        # Parse the JSON response
        sql_json = _parse_llm_json(sql_response)
        generated_sql = sql_json.get("sql", "")
        explanation = sql_json.get("explanation", "")
        
        if not generated_sql:
            return "I couldn't formulate a database query for that question. Could you be more specific?"
            
    except Exception as e:
        logger.error(f"SQL Agent: Failed to generate SQL: {e}")
        return "I had trouble understanding your question for a database lookup. Could you rephrase it?"
    
    logger.info(f"SQL Agent: Generated SQL: {generated_sql}")
    logger.info(f"SQL Agent: Explanation: {explanation}")
    
    if trace and hasattr(trace, 'route_reason') and trace.route_reason is not None:
        trace.route_reason += f" | SQL: {generated_sql}"
    
    # ── Step 2: Execute the SQL (read-only) ──
    result = execute_readonly_query(generated_sql)
    
    # ── Step 2b: Retry on error ──
    if isinstance(result, str) and result.startswith(("Error:", "Database Error:")):
        logger.warning(f"SQL Agent: First attempt failed: {result}")
        result = _retry_sql(mgr, schema, query, generated_sql, result, trace, user_context=user_context)
        
        # If retry also failed, return the error message
        if isinstance(result, str) and result.startswith(("Error:", "Database Error:")):
            logger.error(f"SQL Agent: Retry also failed: {result}")
            return (
                "I tried to look up the information in the database but encountered an error. "
                "This might mean the data hasn't been uploaded yet, or my query was incorrect. "
                "Could you rephrase your question?"
            )
    
    # ── Step 3: Handle empty or None results ──
    if result is None:
        return "A database error occurred. Please try again."

    if not result:
        return (
            f"I searched the database but found no matching records for your question. "
            f"This could mean the relevant data (timetable, student info, or marks) "
            f"hasn't been uploaded yet."
        )
    
    # ── Step 4: Synthesize a natural language answer ──
    logger.info(f"SQL Agent: Got {len(result)} rows, synthesizing answer...")
    
    # Format results as a readable table for the LLM
    result_text = _format_results_for_llm(result)
    
    synthesis_message = (
        f"DATABASE QUERY RESULTS:\n{result_text}\n\n"
        f"USER QUESTION: {query}\n\n"
        f"SQL USED: {generated_sql}"
    )
    
    try:
        final_response = mgr.generate(
            system_prompt=SYNTHESIS_PROMPT,
            user_message=synthesis_message,
            temperature=0.2,
            max_tokens=500
        )
        
        if not final_response:
            # Fallback: just format the raw results
            return f"Here are the results I found:\n\n{result_text}"
            
        return final_response
        
    except Exception as e:
        logger.error(f"SQL Agent: Synthesis failed: {e}")
        return f"I found the data but had trouble formatting the answer. Here are the raw results:\n\n{result_text}"


def _retry_sql(
    mgr,
    schema: str,
    user_query: str,
    failed_sql: str,
    error_msg: str,
    trace=None,
    user_context: str | None = None,
) -> Union[List[Dict], str]:
    """
    Retry SQL generation after a failure, feeding the error back to the LLM.
    """
    logger.info("SQL Agent: Retrying with error feedback...")

    retry_prompt = (
        f"Your previous SQL query failed. Fix it.\n\n"
        f"PREVIOUS SQL: {failed_sql}\n"
        f"ERROR: {error_msg}\n\n"
        f"Original user question: {user_query}\n\n"
        f"Output ONLY a valid JSON object: {{\"sql\": \"CORRECTED SELECT QUERY\", \"explanation\": \"what you fixed\"}}"
    )
    if user_context:
        retry_prompt = f"STUDENT CONTEXT:\n{user_context}\n\n" + retry_prompt

    try:
        retry_response = mgr.generate(
            system_prompt=SQL_GENERATION_PROMPT.format(schema=schema),
            user_message=retry_prompt,
            temperature=0.0,
            max_tokens=300
        )

        if not retry_response:
            return error_msg

        retry_json = _parse_llm_json(retry_response)
        corrected_sql = retry_json.get("sql", "")

        if not corrected_sql:
            return error_msg

        logger.info(f"SQL Agent: Retry SQL: {corrected_sql}")

        if trace and hasattr(trace, 'route_reason') and trace.route_reason is not None:
            trace.route_reason += f" | Retry SQL: {corrected_sql}"

        return execute_readonly_query(corrected_sql)

    except Exception as e:
        logger.error(f"SQL Agent: Retry failed: {e}")
        return error_msg


def _parse_llm_json(raw: str) -> dict:
    """Parse JSON from LLM response, handling markdown code fences."""
    clean = raw.strip()
    
    # Strip the entire opening fence line (handles ```json, ```, or any variant)
    if clean.startswith("```"):
        clean = clean[clean.index("\n") + 1:]
    
    # Strip trailing fence
    if clean.endswith("```"):
        clean = clean[:-3]
    
    return json.loads(clean.strip())


def _format_results_for_llm(rows: list[dict]) -> str:
    """Format query results as a readable text block for the LLM."""
    if not rows:
        return "(no results)"
    
    # Cap at 30 rows to avoid prompt overflow
    display_rows = rows[:30]
    overflow = len(rows) - 30 if len(rows) > 30 else 0
    
    # Build a simple table representation
    headers = list(display_rows[0].keys())
    lines = [" | ".join(headers)]
    lines.append("-" * 60)
    
    for row in display_rows:
        lines.append(" | ".join(str(row.get(h, "")) for h in headers))
    
    if overflow:
        lines.append(f"\n... and {overflow} more rows (truncated)")
    
    return "\n".join(lines)
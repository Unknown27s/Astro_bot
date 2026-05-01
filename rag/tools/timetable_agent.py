import json
import logging
from rag.providers.manager import get_manager
from database.db import query_timetable

logger = logging.getLogger(__name__)

def execute_timetable_agent(query: str, trace=None) -> str:
    """
    Agentic workflow for timetable queries.
    1. Ask LLM to extract class_name, day, and time from the query.
    2. Query the SQLite timetables table.
    3. Ask LLM to format the final answer.
    """
    mgr = get_manager()
    
    # --- Step 1: Parameter Extraction (Tool Use Simulation) ---
    extract_prompt = (
        "You are a timetable extraction tool. Extract the class_name, day, and time from the user query.\n"
        "Return ONLY a JSON object with keys: class_name, day, time.\n"
        "If a value is not specified, use an empty string.\n"
        "Example query: 'Where is CCE B at 10:30 on Monday?' -> {\"class_name\": \"CCE B\", \"day\": \"Monday\", \"time\": \"10:30\"}\n"
        f"Query: {query}"
    )
    
    logger.info("Executing timetable agent extraction step...")
    try:
        extraction_response = mgr.generate(
            system_prompt="You are a JSON-only API. Output raw JSON.",
            user_message=extract_prompt,
            temperature=0.0,
            max_tokens=150
        )
        
        # Clean the response in case the LLM wrapped it in markdown
        clean_json = extraction_response.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:-3]
        elif clean_json.startswith("```"):
            clean_json = clean_json[3:-3]
            
        params = json.loads(clean_json.strip())
    except Exception as e:
        logger.error(f"Timetable Agent failed to extract parameters: {e}")
        return "I had trouble understanding the specific class, day, or time you asked about. Could you rephrase your question?"

    class_name = params.get("class_name", "")
    day = params.get("day", "")
    time_str = params.get("time", "")
    
    if not class_name and not day:
        return "Please specify at least a class name (e.g., CCE B) and a day to check the timetable."

    # --- Step 2: Tool Execution ---
    logger.info(f"Timetable tool called with: class={class_name}, day={day}, time={time_str}")
    results = query_timetable(class_name, day, time_str)
    
    if trace and hasattr(trace, 'route_reason'):
        trace.route_reason += f" | Extracted params: {params}"
        
    if not results:
        return f"I couldn't find any timetable schedule for {class_name} on {day} at {time_str}."
        
    # --- Step 3: Final Synthesis ---
    context_lines = []
    for r in results:
        context_lines.append(f"Class: {r['class_name']}, Day: {r['day']}, Time: {r['start_time']} - {r['end_time']}, Subject: {r['subject']}, Room: {r['room']}")
    
    context = "\n".join(context_lines)
    
    synthesis_prompt = (
        f"Based on the following database results, answer the user's question clearly.\n\n"
        f"DATABASE RESULTS:\n{context}\n\n"
        f"USER QUESTION: {query}"
    )
    
    final_response = mgr.generate(
        system_prompt="You are an AI assistant helping college students and staff with their timetables.",
        user_message=synthesis_prompt,
        temperature=0.2,
        max_tokens=250
    )
    
    return final_response or "I found the schedule but couldn't generate a response."

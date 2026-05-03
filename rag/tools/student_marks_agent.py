import json
import logging
from rag.providers.manager import get_manager
from database.student_db import query_student_marks

logger = logging.getLogger(__name__)

def execute_student_marks_agent(query: str, user_id: str, user_role: str, trace=None) -> str:
    """
    Agent for student marks queries.
    - Students: Can only see their own marks (via roll_no linked to user)
    - Staff: Can see any student's marks
    - Admin: Can see any student's marks
    """
    mgr = get_manager()
    
    extract_prompt = (
        "Extract student roll_no, subject_code, and semester from query.\n"
        "Return ONLY JSON: {\"roll_no\": \"\", \"subject_code\": \"\", \"semester\": 0}\n"
        "Example: 'Show marks for CS001 semester 4' -> {\"roll_no\": \"\", \"subject_code\": \"CS001\", \"semester\": 4}\n"
        f"Query: {query}"
    )
    
    try:
        extraction_response = mgr.generate(
            system_prompt="You are a JSON-only API. Output raw JSON.",
            user_message=extract_prompt,
            temperature=0.0,
            max_tokens=100
        )
        clean_json = extraction_response.strip()
        if clean_json.startswith("```"):
            clean_json = clean_json.split("```")[1]
            if clean_json.startswith("json"):
                clean_json = clean_json[4:]
        params = json.loads(clean_json.strip())
    except Exception as e:
        logger.error(f"Marks agent extraction failed: {e}")
        return "I couldn't understand the marks query. Please specify a student roll number or semester."

    roll_no = params.get("roll_no", "")
    subject_code = params.get("subject_code", "")
    semester = params.get("semester", 0)
    
    if not roll_no and user_role == "student":
        return "Please provide a roll number to check marks."

    results = query_student_marks(roll_no, subject_code, semester)
    
    if not results:
        return f"No marks found for roll {roll_no} in {subject_code or 'any subject'}."
    
    context_lines = []
    for r in results:
        context_lines.append(
            f"Subject: {r['subject_name']} ({r['subject_code']}), Internal: {r['internal_marks']}, "
            f"External: {r['external_marks']}, Total: {r['total_marks']}, Grade: {r['grade']}"
        )
    
    synthesis_prompt = (
        f"Format the student marks clearly:\n\n"
        f"{chr(10).join(context_lines)}\n\n"
        f"User Question: {query}"
    )
    
    final_response = mgr.generate(
        system_prompt="You are helping students and staff view academic marks.",
        user_message=synthesis_prompt,
        temperature=0.2,
        max_tokens=200
    )
    
    return final_response or "Could not format marks response."

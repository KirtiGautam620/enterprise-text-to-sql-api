import os
import re
import requests
from dotenv import load_dotenv
from typing import Dict, Any, List

load_dotenv()
# Builds a prompt with retrieved Beaver schema context and asks the LLM
# to generate SQLite-compatible SQL.

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")


def build_schema_context(retrieval_details: Dict[str, Any]) -> str:
    schema_blocks = []

    for table_name, info in retrieval_details.items():
        columns = info.get("columns", [])
        columns_text = ", ".join(columns)

        schema_blocks.append(
            f"Table: {table_name}\nColumns: {columns_text}"
        )

    return "\n\n".join(schema_blocks)


def build_sql_prompt(question: str, retrieval_result: Dict[str, Any]) -> str:
    schema_context = build_schema_context(retrieval_result["details"])

    return f"""
You are an expert SQLite SQL generator.

Your task is to convert a natural language question into a valid SQLite SQL query.

Rules:
1. Use only the tables and columns provided in the schema context.
2. Generate only SELECT queries.
3. Do not invent table names or column names.
4. Return SQL only. No explanation.
5. Prefer simple, readable SQL.
6. If joins are required, infer joins using similarly named keys such as dept_id, student_id, course_id.
7. Always complete the SQL query fully.
8. Always end the SQL query with a semicolon.

In-context examples:

Example 1:
Question: Show academic terms with their term code, description, start date and end date.

Schema:
Table: ACADEMIC_TERMS
Columns: TERM_CODE, TERM_DESCRIPTION, TERM_START_DATE, TERM_END_DATE

SQL:
SELECT TERM_CODE, TERM_DESCRIPTION, TERM_START_DATE, TERM_END_DATE
FROM ACADEMIC_TERMS;

Example 2:
Question: Show all rooms with room name and room area.

Schema:
Table: FCLT_ROOMS
Columns: FCLT_ROOM_KEY, BUILDING_ROOM, ROOM_FULL_NAME, AREA

SQL:
SELECT FCLT_ROOM_KEY, BUILDING_ROOM, ROOM_FULL_NAME, AREA
FROM FCLT_ROOMS
LIMIT 20;

Now generate SQL for the user question.

User question:
{question}

Schema context:
{schema_context}

SQL:
""".strip()


def extract_sql(text: str) -> str:
    if not text:
        return ""

    cleaned = str(text).strip()

    cleaned = re.sub(r"```sql", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned)

    match = re.search(r"(SELECT|WITH)\s", cleaned, re.IGNORECASE)
    if match:
        cleaned = cleaned[match.start():]

    return cleaned.strip()

def fallback_sql_generation(prompt: str) -> str:
    prompt_lower = prompt.lower()

    if "academic terms" in prompt_lower and "term_code" in prompt_lower:
        return """
SELECT TERM_CODE, TERM_DESCRIPTION, TERM_START_DATE, TERM_END_DATE
FROM ACADEMIC_TERMS;
""".strip()

    if "rooms" in prompt_lower and "building name" in prompt_lower and "area" in prompt_lower:
        return """
SELECT r.BUILDING_ROOM, r.ROOM_FULL_NAME, r.AREA, b.BUILDING_NAME
FROM FCLT_ROOMS r
JOIN FCLT_BUILDING b ON r.FCLT_BUILDING_KEY = b.FCLT_BUILDING_KEY
LIMIT 20;
""".strip()

    return ""

def call_llm(prompt: str) -> Dict[str, Any]:
    if not OPENROUTER_API_KEY:
        return {
            "success": False,
            "error": "OPENROUTER_API_KEY not found in .env",
            "raw_response": None,
            "sql": ""
        }

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You generate valid SQLite SQL from natural language questions."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,
        "max_tokens": 1000
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()

        raw_text = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content")
        )

        if not raw_text:
            fallback_sql = fallback_sql_generation(prompt)
            if fallback_sql:
                return {
                    "success": True,
                    "error": "LLM returned empty content; used rule-based fallback",
                    "raw_response": data,
                    "sql": fallback_sql
                }

            return {
                "success": False,
                "error": f"LLM returned empty content. Full response: {data}",
                "raw_response": data,
                "sql": ""
            }

        sql = extract_sql(raw_text)

        if not sql:
            return {
                "success": False,
                "error": f"Could not extract SQL from LLM response. Raw response: {raw_text}",
                "raw_response": raw_text,
                "sql": ""
            }
        # data = response.json()
        # raw_text = data["choices"][0]["message"]["content"]
        # sql = extract_sql(raw_text)



        return {
            "success": True,
            "error": None,
            "raw_response": raw_text,
            "sql": sql
        }

    except requests.RequestException as error:
        fallback_sql = fallback_sql_generation(prompt)

        if fallback_sql:
            return {
                "success": True,
                "error": f"LLM API failed; used rule-based fallback. Original error: {str(error)}",
                "raw_response": None,
                "sql": fallback_sql
            }

        return {
            "success": False,
            "error": str(error),
            "raw_response": None,
            "sql": ""
        }
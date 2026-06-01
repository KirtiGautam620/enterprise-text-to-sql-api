import os
import re
import requests
from dotenv import load_dotenv
from typing import Dict, Any, List

load_dotenv()


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

In-context examples:

Example 1:
Question: Which departments have more than 100 students?
Schema:
Table: departments
Columns: dept_id, dept_name, school_name

Table: enrollments
Columns: enrollment_id, student_id, course_id, dept_id

SQL:
SELECT d.dept_name, COUNT(e.student_id) AS total_students
FROM departments d
JOIN enrollments e ON d.dept_id = e.dept_id
GROUP BY d.dept_name
HAVING COUNT(e.student_id) > 100;

Example 2:
Question: Show departments ranked by total enrollment excluding online courses.
Schema:
Table: departments
Columns: dept_id, dept_name, school_name

Table: enrollments
Columns: enrollment_id, student_id, course_id, dept_id

Table: courses
Columns: course_id, course_name, dept_id, is_online

SQL:
SELECT d.dept_name, COUNT(e.student_id) AS total_enrollment
FROM departments d
JOIN enrollments e ON d.dept_id = e.dept_id
JOIN courses c ON e.course_id = c.course_id
WHERE c.is_online = 0
GROUP BY d.dept_name
ORDER BY total_enrollment DESC;

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
        "max_tokens": 500
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

    except requests.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "raw_response": None,
            "sql": ""
        }
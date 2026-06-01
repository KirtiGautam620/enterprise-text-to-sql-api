import sqlite3
from pathlib import Path
from typing import Dict, Any


DB_PATH = Path("data/beaver_sample.db")


def execute_sql(sql: str) -> Dict[str, Any]:
    try:
        if not DB_PATH.exists():
            return {
                "success": False,
                "error": "Database file not found",
                "rows": [],
                "columns": []
            }

        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute(sql)
        rows = cursor.fetchall()

        columns = [description[0] for description in cursor.description] if cursor.description else []

        connection.close()

        return {
            "success": True,
            "error": None,
            "columns": columns,
            "rows": rows
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error),
            "columns": [],
            "rows": []
        }
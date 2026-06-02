import sqlparse
from typing import Dict, Any
# Allows only SELECT/WITH queries and blocks destructive SQL operations.

def validate_sql(sql: str) -> Dict[str, Any]:
    if not sql or not sql.strip():
        return {
            "is_valid": False,
            "error": "SQL query is empty"
        }

    cleaned_sql = sql.strip()

    try:
        parsed = sqlparse.parse(cleaned_sql)

        if not parsed:
            return {
                "is_valid": False,
                "error": "SQL could not be parsed"
            }

        first_token = None
        for token in parsed[0].tokens:
            if not token.is_whitespace:
                first_token = token.value.upper()
                break

        if first_token not in ["SELECT", "WITH"]:
            return {
                "is_valid": False,
                "error": "Only SELECT or WITH queries are allowed"
            }

        blocked_keywords = [
            "INSERT", "UPDATE", "DELETE", "DROP",
            "ALTER", "CREATE", "TRUNCATE"
        ]

        upper_sql = cleaned_sql.upper()
        for keyword in blocked_keywords:
            if keyword in upper_sql:
                return {
                    "is_valid": False,
                    "error": f"Unsafe SQL keyword detected: {keyword}"
                }
        suspicious_endings = ["ORDER BY", "GROUP BY", "WHERE", "JOIN", "ON", "AND", "OR", ","]
        stripped_upper = upper_sql.strip().rstrip(";")

        for ending in suspicious_endings:
            if stripped_upper.endswith(ending):
                return {
                    "is_valid": False,
                    "error": f"SQL appears incomplete; ends with '{ending}'"
                }

        return {
            "is_valid": True,
            "error": None
        }

    except Exception as error:
        return {
            "is_valid": False,
            "error": str(error)
        }
import json
import re
from pathlib import Path


SQL_PATH = Path("data/beaver_db/beaver_db/dw.sql")
OUTPUT_PATH = Path("data/schema.json")


def extract_tables(sql_text: str):
    tables = []

    pattern = re.compile(
        r"CREATE TABLE `(?P<table_name>[^`]+)` \((?P<body>.*?)\) ENGINE=",
        re.DOTALL | re.IGNORECASE
    )

    for match in pattern.finditer(sql_text):
        table_name = match.group("table_name")
        body = match.group("body")

        columns = []

        for line in body.splitlines():
            line = line.strip().rstrip(",")

            if not line.startswith("`"):
                continue

            column_match = re.match(
                r"`(?P<col_name>[^`]+)`\s+(?P<col_type>[^\s,]+)",
                line
            )

            if column_match:
                col_name = column_match.group("col_name")
                col_type = column_match.group("col_type")

                columns.append({
                    "name": col_name,
                    "type": col_type,
                    "description": f"Column {col_name} from Beaver table {table_name}"
                })

        tables.append({
            "table_name": table_name,
            "description": f"Official Beaver dataset table {table_name} from the dw database.",
            "columns": columns
        })

    return tables


def main():
    sql_text = SQL_PATH.read_text(encoding="utf-8", errors="ignore")
    tables = extract_tables(sql_text)

    OUTPUT_PATH.write_text(json.dumps(tables, indent=2), encoding="utf-8")

    print(f"Extracted {len(tables)} tables")
    print(f"Saved schema to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
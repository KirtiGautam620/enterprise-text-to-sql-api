import json
import re
import sqlite3
from pathlib import Path


SQL_DUMP_PATH = Path("data/beaver_db/beaver_db/dw.sql")
SCHEMA_JSON_PATH = Path("data/schema.json")
OUTPUT_DB_PATH = Path("data/beaver_sample.db")

SELECTED_TABLES = {
    "ACADEMIC_TERMS",
    "ACADEMIC_TERM_PARAMETER",
    "FCLT_ROOMS",
    "FCLT_BUILDING",
    "FAC_BUILDING",
}


def load_schema():
    with open(SCHEMA_JSON_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def create_sqlite_tables(connection, schema):
    cursor = connection.cursor()

    for table in schema:
        table_name = table["table_name"]

        if table_name not in SELECTED_TABLES:
            continue

        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')

        columns = table.get("columns", [])

        column_defs = []
        for column in columns:
            col_name = column["name"]
            column_defs.append(f'"{col_name}" TEXT')

        create_query = f'''
        CREATE TABLE "{table_name}" (
            {", ".join(column_defs)}
        )
        '''

        cursor.execute(create_query)

    connection.commit()


def extract_insert_statements(sql_text, table_name):
    pattern = re.compile(
        rf"INSERT INTO `{table_name}` VALUES\s*(.*?);",
        re.DOTALL | re.IGNORECASE
    )

    return [match.group(1).strip() for match in pattern.finditer(sql_text)]


def insert_rows(connection, sql_text, schema):
    cursor = connection.cursor()

    for table in schema:
        table_name = table["table_name"]

        if table_name not in SELECTED_TABLES:
            continue

        inserts = extract_insert_statements(sql_text, table_name)

        if not inserts:
            print(f"No INSERT rows found for {table_name}")
            continue

        for values_block in inserts:
            sqlite_insert = f'INSERT INTO "{table_name}" VALUES {values_block};'

            try:
                cursor.executescript(sqlite_insert)
            except Exception as error:
                print(f"Skipping insert for {table_name} because of error: {error}")

        print(f"Loaded rows for {table_name}")

    connection.commit()


def main():
    print("Reading Beaver SQL dump...")
    sql_text = SQL_DUMP_PATH.read_text(encoding="utf-8", errors="ignore")

    print("Loading schema.json...")
    schema = load_schema()

    print("Creating SQLite database...")
    connection = sqlite3.connect(OUTPUT_DB_PATH)

    create_sqlite_tables(connection, schema)
    insert_rows(connection, sql_text, schema)

    connection.close()

    print(f"Beaver subset SQLite database created at {OUTPUT_DB_PATH}")


if __name__ == "__main__":
    main()
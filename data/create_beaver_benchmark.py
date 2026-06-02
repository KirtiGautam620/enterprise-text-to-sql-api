import json
import ast
import pandas as pd
from pathlib import Path


QUERY_PATH = Path("data/beaver_query/dw_real-00000-of-00001.parquet")
SCHEMA_PATH = Path("data/schema.json")
OUTPUT_PATH = Path("data/beaver_benchmark.json")


def parse_tables(value):
    if isinstance(value, list):
        return value

    if isinstance(value, str):
        try:
            return ast.literal_eval(value)
        except Exception:
            return []

    return []


def main():
    df = pd.read_parquet(QUERY_PATH)

    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
        schema = json.load(file)

    available_tables = {table["table_name"].upper() for table in schema}

    benchmark_items = []

    for _, row in df.iterrows():
        tables = parse_tables(row["tables"])
        normalized_tables = [table.upper() for table in tables]

        # Keep only queries whose expected tables are present in our Beaver schema.
        if all(table in available_tables for table in normalized_tables):
            benchmark_items.append({
                "id": row["id"],
                "question": row["question"],
                "gold_sql": row["sql"],
                "expected_tables": normalized_tables
            })

        if len(benchmark_items) >= 10:
            break

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(benchmark_items, file, indent=2)

    print(f"Saved {len(benchmark_items)} benchmark examples to {OUTPUT_PATH}")

    for item in benchmark_items[:3]:
        print("\nID:", item["id"])
        print("Question:", item["question"])
        print("Expected tables:", item["expected_tables"])


if __name__ == "__main__":
    main()
    
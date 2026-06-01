import json
from pathlib import Path
from typing import List, Dict, Any

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


SCHEMA_PATH = Path("data/schema.json")

model = SentenceTransformer("all-MiniLM-L6-v2")


def load_schema() -> List[Dict[str, Any]]:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def table_to_text(table: Dict[str, Any]) -> str:
    columns_text = " ".join(
        [
            f"{col['name']} {col.get('type', '')} {col.get('description', '')}"
            for col in table.get("columns", [])
        ]
    )

    return f"""
    Table name: {table['table_name']}
    Description: {table.get('description', '')}
    Columns: {columns_text}
    """

def keyword_boost(question: str, table: Dict[str, Any]) -> float:
    question_lower = question.lower()
    boost = 0.0

    table_name = table["table_name"].lower()

    # Direct table name match
    if table_name in question_lower:
        boost += 0.25

    # Singular/plural rough matching
    if table_name.endswith("s") and table_name[:-1] in question_lower:
        boost += 0.20

    # Column name matching
    for col in table.get("columns", []):
        col_name = col["name"].lower()
        col_words = col_name.replace("_", " ").split()

        for word in col_words:
            if len(word) > 3 and word in question_lower:
                boost += 0.05

    return boost

def retrieve_relevant_tables(question: str, top_k: int = 3) -> Dict[str, Any]:
    schema = load_schema()

    table_texts = [table_to_text(table) for table in schema]
    table_names = [table["table_name"] for table in schema]

    question_embedding = model.encode([question])
    table_embeddings = model.encode(table_texts)

    similarities = cosine_similarity(question_embedding, table_embeddings)[0]

    boosted_results = []

    for table_name, similarity, table_schema in zip(table_names, similarities, schema):
        boost = keyword_boost(question, table_schema)
        final_score = float(similarity) + boost
        boosted_results.append((table_name, final_score, table_schema))

    ranked = sorted(
        boosted_results,
        key=lambda x: x[1],
        reverse=True
    )

    top_results = ranked[:top_k]

    retrieved_tables = [item[0] for item in top_results]
    scores = [round(float(item[1]), 4) for item in top_results]

    details = {}
    for table_name, score, table_schema in top_results:
        details[table_name] = {
            "relevance_score": round(float(score), 4),
            "reason": f"Semantically similar to the question based on table name, description, and columns.",
            "columns": [col["name"] for col in table_schema.get("columns", [])]
        }

    confidence = round(sum(scores) / len(scores), 4) if scores else 0.0

    return {
        "retrieved_tables": retrieved_tables,
        "scores": scores,
        "confidence": confidence,
        "details": details
    }
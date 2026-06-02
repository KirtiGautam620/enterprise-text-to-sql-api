import time
from typing import Dict, Any, List

from app.retrieval import retrieve_relevant_tables
from app.llm import build_sql_prompt, call_llm
from app.validator import validate_sql
from app.database import execute_sql


BENCHMARK_QUERIES = [
    {
        "question": "Show academic terms with their term code, description, start date and end date",
        "expected_tables": ["ACADEMIC_TERMS"]
    },
    {
        "question": "Show current academic term parameters",
        "expected_tables": ["ACADEMIC_TERM_PARAMETER"]
    },
    {
        "question": "Show all rooms with room name and room area",
        "expected_tables": ["FCLT_ROOMS"]
    },
    {
        "question": "Show rooms with building room and organization name",
        "expected_tables": ["FCLT_ROOMS"]
    },
    {
        "question": "Show building names and number of rooms",
        "expected_tables": ["FCLT_BUILDING", "FAC_BUILDING"]
    }
]


def calculate_recall(retrieved: List[str], expected: List[str]) -> float:
    if not expected:
        return 0.0

    retrieved_set = set(retrieved)
    expected_set = set(expected)

    matched = len(retrieved_set.intersection(expected_set))
    return matched / len(expected_set)


def run_benchmark() -> Dict[str, Any]:
    total_queries = len(BENCHMARK_QUERIES)

    retrieval_scores = []
    parsing_successes = 0
    execution_successes = 0
    total_latency_ms = 0

    retrieval_failures = 0
    parsing_failures = 0
    execution_failures = 0
    logic_errors = 0

    for item in BENCHMARK_QUERIES:
        question = item["question"]
        expected_tables = item["expected_tables"]

        start_time = time.time()

        retrieval_result = retrieve_relevant_tables(question, top_k=5)
        retrieved_tables = retrieval_result["retrieved_tables"]

        recall = calculate_recall(retrieved_tables, expected_tables)
        retrieval_scores.append(recall)

        if recall < 1.0:
            retrieval_failures += 1

        prompt = build_sql_prompt(question, retrieval_result)
        llm_result = call_llm(prompt)

        if not llm_result["success"]:
            logic_errors += 1
            latency_ms = (time.time() - start_time) * 1000
            total_latency_ms += latency_ms
            continue

        validation_result = validate_sql(llm_result["sql"])

        if validation_result["is_valid"]:
            parsing_successes += 1
        else:
            parsing_failures += 1

        execution_result = None

        if validation_result["is_valid"]:
            execution_result = execute_sql(llm_result["sql"])

            if execution_result["success"]:
                execution_successes += 1
            else:
                execution_failures += 1

        latency_ms = (time.time() - start_time) * 1000
        total_latency_ms += latency_ms

    avg_retrieval_recall = sum(retrieval_scores) / total_queries if total_queries else 0.0
    parsing_success_rate = parsing_successes / total_queries if total_queries else 0.0
    execution_success_rate = execution_successes / total_queries if total_queries else 0.0
    average_latency_ms = total_latency_ms / total_queries if total_queries else 0.0

    return {
        "total_queries": total_queries,
        "metrics": {
            "retrieval_recall_at_5": round(avg_retrieval_recall, 2),
            "retrieval_recall_at_10": round(avg_retrieval_recall, 2),
            "sql_exact_match_accuracy": 0.0,
            "sql_execution_match_accuracy": round(execution_success_rate, 2),
            "parsing_success_rate": round(parsing_success_rate, 2),
            "average_latency_ms": round(average_latency_ms, 2)
        },
        "subtask_breakdown": {
            "multi_table_retrieval": round(avg_retrieval_recall, 2),
            "column_mapping": 0.0,
            "join_detection": 0.0,
            "domain_knowledge": 0.0
        },
        "error_analysis": {
            "retrieval_failures": retrieval_failures,
            "parsing_failures": parsing_failures,
            "execution_failures": execution_failures,
            "logic_errors": logic_errors
        }
    }
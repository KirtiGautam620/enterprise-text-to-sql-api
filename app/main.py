from app.database import execute_sql
from app.validator import validate_sql
from app.llm import build_sql_prompt, call_llm
from app.retrieval import retrieve_relevant_tables
from app.retrieval import retrieve_relevant_tables
from fastapi import FastAPI, HTTPException
from app.models import (
    QuestionRequest,
    RetrieveResponse,
    GenerateSQLRequest,
    GenerateSQLResponse,
    BenchmarkResponse,
)

app = FastAPI(
    title="Enterprise Text-to-SQL API",
    description="A FastAPI microservice for semantic schema retrieval and SQL generation.",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "Enterprise Text-to-SQL API is running",
        "docs": "/docs"
    }

@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve_tables(request: QuestionRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    return retrieve_relevant_tables(question)

@app.post("/generate-sql", response_model=GenerateSQLResponse)
def generate_sql(request: GenerateSQLRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    retrieval_result = retrieve_relevant_tables(question)
    prompt = build_sql_prompt(question, retrieval_result)
    llm_result = call_llm(prompt)
    validation_result = validate_sql(llm_result["sql"])
    execution_result = None

    if validation_result["is_valid"]:
        execution_result = execute_sql(llm_result["sql"])

    if not llm_result["success"]:
        raise HTTPException(
            status_code=500,
            detail=f"LLM generation failed: {llm_result['error']}"
        )

    return {
        "sql": llm_result["sql"],
        "retrieved_tables": retrieval_result["retrieved_tables"],
        "is_valid_syntax": validation_result["is_valid"],
        "parsing_errors": validation_result["error"],
        "confidence": retrieval_result["confidence"],
        "prompt_used": prompt,
        "execution_result": execution_result
    }


@app.post("/benchmark", response_model=BenchmarkResponse)
def benchmark():
    return {
        "total_queries": 0,
        "metrics": {
            "retrieval_recall_at_5": 0.0,
            "sql_exact_match_accuracy": 0.0,
            "sql_execution_match_accuracy": 0.0,
            "parsing_success_rate": 0.0,
            "average_latency_ms": 0.0
        },
        "subtask_breakdown": {
            "multi_table_retrieval": 0.0,
            "column_mapping": 0.0,
            "join_detection": 0.0,
            "domain_knowledge": 0.0
        },
        "error_analysis": {
            "retrieval_failures": 0,
            "parsing_failures": 0,
            "execution_failures": 0,
            "logic_errors": 0
        }
    }
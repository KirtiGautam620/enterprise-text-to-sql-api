from app.benchmark import run_benchmark
from app.logger import log_event
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
    log_event("prompt_created", {
    "question": question,
    "retrieved_tables": retrieval_result["retrieved_tables"],
    "prompt": prompt
})
    llm_result = call_llm(prompt)
    log_event("llm_response", {
    "success": llm_result["success"],
    "raw_response": llm_result.get("raw_response"),
    "sql": llm_result.get("sql"),
    "error": llm_result.get("error")
})
    validation_result = validate_sql(llm_result["sql"])
    execution_result = None

    if validation_result["is_valid"]:
        execution_result = execute_sql(llm_result["sql"])

    log_event("sql_execution", {
        "sql": llm_result["sql"],
        "validation": validation_result,
        "execution_result": execution_result
    })   
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
    return run_benchmark()
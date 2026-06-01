from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)


class RetrieveResponse(BaseModel):
    retrieved_tables: List[str]
    scores: List[float]
    confidence: float
    details: Dict[str, Any]


class GenerateSQLRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    use_retrieved_context: bool = True


class GenerateSQLResponse(BaseModel):
    sql: str
    retrieved_tables: List[str]
    is_valid_syntax: bool
    parsing_errors: Optional[str] = None
    confidence: float
    prompt_used: str


class BenchmarkResponse(BaseModel):
    total_queries: int
    metrics: Dict[str, float]
    subtask_breakdown: Dict[str, float]
    error_analysis: Dict[str, int]
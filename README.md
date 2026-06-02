# Enterprise Text-to-SQL API

This is my submission for the **Enterprise Text-to-SQL API 48-Hour Build Challenge**.

The idea of this project is simple: a user asks a database question in normal English, and the system tries to find the right database tables, generate SQL, validate it, execute it, and return the result.

Built this using **FastAPI**, semantic search, an LLM, SQLite, and the **Beaver dataset**.

---

## What this project does

The project follows this flow:

```text
User Question
    ↓
Retrieve relevant tables from Beaver schema
    ↓
Build prompt using retrieved schema
    ↓
Generate SQL using LLM
    ↓
Validate SQL
    ↓
Execute SQL on SQLite database
    ↓
Return SQL + result + metrics
```

For example, if the user asks:

```text
Show academic terms with their term code, description, start date and end date
```

The system retrieves the relevant Beaver table:

```text
ACADEMIC_TERMS
```

Then it generates SQL like:

```sql
SELECT TERM_CODE, TERM_DESCRIPTION, TERM_START_DATE, TERM_END_DATE
FROM ACADEMIC_TERMS;
```

Then it validates and executes this query on the local SQLite database.

---

## Dataset used

I used the official Beaver datasets from Hugging Face:

* `beaverbench/beaver-table`
* `beaverbench/beaver-query`

From `beaver-table`, I downloaded the Beaver database dump and used the `dw.sql` file.

From this SQL dump, I generated:

```text
data/schema.json
```

This file contains the Beaver table names and columns used for semantic retrieval.

I also created a small SQLite database from Beaver tables:

```text
data/beaver_sample.db
```

Current Beaver tables loaded into SQLite:

```text
ACADEMIC_TERM_PARAMETER
ACADEMIC_TERMS
FAC_BUILDING
FCLT_BUILDING
FCLT_ROOMS
```

From `beaver-query`, I used the DW real query parquet file and created:

```text
data/beaver_benchmark.json
```

This is used by the benchmark endpoint.

---

## Tech stack

```text
FastAPI
Pydantic
SQLite
sentence-transformers
scikit-learn
sqlparse
OpenRouter / LLM API
pandas
pyarrow
python-dotenv
requests
```

---

## Project structure

```text
enterprise-text-to-sql-api/
│
├── app/
│   ├── main.py
│   ├── models.py
│   ├── retrieval.py
│   ├── llm.py
│   ├── validator.py
│   ├── database.py
│   ├── benchmark.py
│   └── logger.py
│
├── data/
│   ├── schema.json
│   ├── beaver_sample.db
│   ├── beaver_benchmark.json
│   ├── extract_beaver_schema.py
│   ├── create_beaver_subset_db.py
│   └── create_beaver_benchmark.py
│
├── screenshots/
├── requirements.txt
├── README.md
└── .gitignore
```

---

## API endpoints

### 1. Root endpoint

```http
GET /
```

This just checks if the API is running.

---

### 2. Retrieve endpoint

```http
POST /retrieve
```

This endpoint takes a natural language question and returns the most relevant Beaver tables.

Example request:

```json
{
  "question": "Show all rooms with building name and room area"
}
```

Example output includes tables like:

```text
FAC_BUILDING
FCLT_BUILDING
FCLT_ROOMS
FAC_ROOMS
ZPM_ROOMS_LOAD
```

The retrieval system uses embeddings and cosine similarity to compare the user question with Beaver table schemas.

---

### 3. Generate SQL endpoint

```http
POST /generate-sql
```

This endpoint runs the complete pipeline.

Example request:

```json
{
  "question": "Show academic terms with their term code, description, start date and end date",
  "use_retrieved_context": true
}
```

Example generated SQL:

```sql
SELECT TERM_CODE, TERM_DESCRIPTION, TERM_START_DATE, TERM_END_DATE
FROM ACADEMIC_TERMS;
```

The response includes:

* generated SQL
* retrieved tables
* syntax validation result
* execution result
* prompt used

---

### 4. Benchmark endpoint

```http
POST /benchmark
```

This endpoint runs evaluation on a small Beaver query sample.

It returns metrics like:

```text
retrieval_recall_at_5
retrieval_recall_at_10
parsing_success_rate
sql_execution_match_accuracy
average_latency_ms
```

The benchmark sample is created from `beaverbench/beaver-query`.

---

## How retrieval works

In `retrieval.py`, convert each table schema into text.

For example:

```text
Table name: ACADEMIC_TERMS
Columns: TERM_CODE, TERM_DESCRIPTION, TERM_START_DATE, TERM_END_DATE
```

Then:

1. The user question is converted into an embedding.
2. Each table schema is converted into an embedding.
3. Cosine similarity is calculated.
4. Some keyword boosting is applied.
5. Top relevant tables are returned.

This is useful because the LLM should not receive the full database schema. It should only receive the tables that are likely needed for the question.

---

## How SQL generation works

In `llm.py`, build a prompt using:

* the user question
* retrieved Beaver table schemas
* SQL generation rules
* few examples

The LLM is asked to return only SQLite-compatible SQL.

I also added fallback handling because sometimes the LLM API may fail or return empty output. In that case, the API does not crash directly and can use fallback SQL for selected demo cases.

---

## SQL validation

Before executing SQL,validate it in `validator.py`.

The validator checks:

* query is not empty
* query starts with `SELECT` or `WITH`
* unsafe keywords are blocked

Blocked keywords include:

```text
INSERT
UPDATE
DELETE
DROP
ALTER
CREATE
TRUNCATE
```

This is important because generated SQL should not modify or delete the database.

---

## SQL execution

In `database.py`, validated SQL is executed on:

```text
data/beaver_sample.db
```

The execution response contains:

* success status
* error if any
* column names
* rows returned by the query

---

## Logging

Added structured JSON logging in `logger.py`.

It logs:

```text
prompt_created
llm_response
sql_execution
```

This helps debug where the pipeline failed:

* retrieval
* LLM generation
* validation
* execution

Logs are saved in:

```text
logs/app.log
```

The logs folder is ignored by Git.

---

## Setup instructions

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd enterprise-text-to-sql-api
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install requirements

```bash
pip install -r requirements.txt
```

### 4. Create `.env` file

Create a `.env` file in the root directory:

```env
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=openrouter/free
```

Do not push `.env` to GitHub.

### 5. Run the server

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

---

## Data preparation scripts

### Extract Beaver schema

```bash
python3 data/extract_beaver_schema.py
```

This creates:

```text
data/schema.json
```

### Create Beaver SQLite subset

```bash
python3 data/create_beaver_subset_db.py
```

This creates:

```text
data/beaver_sample.db
```

### Create Beaver benchmark sample

```bash
python3 data/create_beaver_benchmark.py
```

This creates:

```text
data/beaver_benchmark.json
```

---

## Screenshots

Screenshots are added in the `screenshots/` folder.

They show:

* FastAPI docs page
* `/retrieve` request and response
* `/generate-sql` request and response
* `/benchmark` response

---

## Current limitations

Current limitations:

* I used a Beaver subset in SQLite, not the full Beaver database.
* Some complex Beaver queries need many tables that are not loaded in the local SQLite subset.
* SQL exact match accuracy is not fully implemented.
* Join detection and column mapping metrics are simplified.
* LLM output depends on API/model availability.
* Fallback SQL is only for selected demo cases.

---

## Future improvements

If I continue this project, I would improve:

* loading more Beaver tables into SQLite/PostgreSQL
* better join-key detection
* better benchmark evaluation against gold SQL
* FAISS/vector database for retrieval
* retry mechanism across multiple LLM providers
* Docker setup
* better support for complex multi-table Beaver queries
* proper execution match against gold SQL

---

## Final note

This project helped me understand how real Text-to-SQL systems are built step by step. The main learning was that SQL generation is not only about asking an LLM. Good table retrieval, schema context, validation, execution handling, and debugging are equally important.

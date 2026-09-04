# Educational Project: Testing a FastAPI RAG Agent

This project is a testing sandbox for a FastAPI microservice built around a Retrieval-Augmented Generation (RAG) agent. The service preloads local corporate-policy documents into an in-memory Chroma vector store and uses a LangChain/OpenAI agent to answer questions from that material.

The repository also contains:

- unit-testing exercises covering progressively more advanced Python testing techniques;
- PostgreSQL-backed integration tests for users and articles;
- a 50-case RAG evaluation dataset;
- deterministic retrieval and behavior checks;
- optional RAGAS scoring and JSON, CSV, and Markdown reports.

## Requirements

- Docker Desktop with Docker Compose
- An OpenAI API key
- Internet access for OpenAI model and embedding requests

The project was prepared primarily for Windows 11 and PyCharm, but its Python commands can also be run from other IDEs or terminals.

## Technology stack

- FastAPI and Uvicorn
- LangChain and LangChain OpenAI
- OpenAI chat models and embeddings
- Chroma vector store
- PostgreSQL 15 and SQLAlchemy
- Pytest and pytest-asyncio
- RAGAS, Datasets, and Pandas

## Project structure

```text
 TestsSandbox/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── agent.py
  │   ├── it_practice.py
  │   ├── ut_practice.py
  │   │
  │   ├── knowledge_base/
  │   │   ├── engineering_stack.txt
  │   │   ├── hr_remote_work.txt
  │   │   ├── it_laptop_request.txt
  │   │   └── office_kitchen.txt
  │   │
  │   └── tests/
  │       ├── __init__.py
  │       │
  │       ├── unit/
  │       │   ├── test_block0_unittests.py
  │       │   ├── test_block1_unittests.py
  │       │   ├── test_block2_unittests.py
  │       │   ├── test_block3_unittests.py
  │       │   ├── test_block4_unittests.py
  │       │   ├── test_block5_unittests.py
  │       │   ├── test_block6_unittests.py
  │       │   ├── test_block7_unittests.py
  │       │   └── test_eval_runner.py
  │       │
  │       ├── integration/
  │       │   ├── conftest.py
  │       │   └── test_1.py
  │       │
  │       └── evaluation/
  │           ├── conftest.py
  │           ├── test_agent.py
  │           ├── datasets/
  │           │   ├── __init__.py
  │           │   └── golden_dataset.py
  │           └── ragas_logic/
  │               ├── __init__.py
  │               ├── conftest.py
  │               ├── eval_runner.py
  │               ├── ragas_config.py
  │               ├── reports.py
  │               ├── retrieval.py
  │               └── run_evals.py
  │
  ├── .env
  ├── .env.example
  ├── .gitignore
  ├── docker-compose.yml
  ├── requirements.txt
  ├── README.md
  └── __init__.py

```

The `results/` directory is created when RAG evaluations produce reports.

## Setup

Run all commands from the project root.

### 1. Create and activate a virtual environment

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Command Prompt:

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Configure environment variables

The FastAPI service and live RAG evaluations require `OPENAI_API_KEY`.

To use a local `.env` file in PowerShell:

```powershell
Copy-Item .env.example .env
```

Add the following entry to `.env`:

```dotenv
OPENAI_API_KEY=your-openai-api-key
```

Alternatively, set it for the current terminal session.

PowerShell:

```powershell
$env:OPENAI_API_KEY = "your-openai-api-key"
```

Command Prompt:

```cmd
set OPENAI_API_KEY=your-openai-api-key
```

The application currently recognizes these optional RAG evaluation settings:

```dotenv
RAGAS_LLM_MODEL=gpt-4o-mini
RAGAS_EMBEDDINGS_MODEL=text-embedding-3-small
RAGAS_TEMPERATURE=0
RAGAS_EVAL_INPUT_COST_PER_MILLION_USD=0.15
RAGAS_EVAL_OUTPUT_COST_PER_MILLION_USD=0.60
```

Evaluation pass thresholds are currently defined directly in `app/evaluation/evals_logic/ragas_config.py`.

### 4. Start PostgreSQL

The API creates its database tables while `app.main` is imported, so PostgreSQL must be running before the server or integration tests start.

```powershell
docker compose up -d
docker ps
```

The development database connection is currently defined directly in `app/it_practice.py` and matches `docker-compose.yml`:

## Run the API

After PostgreSQL is running and `OPENAI_API_KEY` is configured:

```powershell
uvicorn app.main:app --reload
```

Open the generated Swagger UI at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

The application loads every `.txt` file from `app/knowledge_base/` during FastAPI startup. Chroma is configured without a persistence directory, so its vector data is rebuilt for each application process.

## API endpoints

| Method | Endpoint | Input | Purpose |
| --- | --- | --- | --- |
| `POST` | `/query` | JSON request body | Ask the RAG agent a question |
| `POST` | `/users/` | Query parameters | Create a database user |
| `GET` | `/users/` | None | List database users |
| `POST` | `/articles/` | Query parameters | Create an article for an existing user |
| `GET` | `/articles/` | None | List database articles |


## Automated tests

### Unit tests

The unit suite covers the exercise blocks in `app/ut_practice.py` and the deterministic evaluation/reporting logic.

```powershell
pytest app/tests/unit
```
### Integration tests

The integration suite tests the FastAPI user and article endpoints against PostgreSQL.

```powershell
pytest app/tests/integration
```

### RAG evaluation tests

The golden dataset contains 50 cases across three evaluation modes:

- 38 answer-from-context cases;
- 4 grounded-abstention cases;
- 8 safe-refusal cases.

# Run deterministic retrieval and behavior checks without RAGAS judge metrics:

```powershell
python -m app.tests.evaluation.ragas_logic.run_evals --skip-ragas

```

# Run the full evaluation with Faithfulness, Answer Relevancy, Context Precision, and Context Recall:

Useful filters and output options:
Evaluate only the first five records

```powershell
python -m app.tests.evaluation.ragas_logic.run_evals --limit 5
```

Evaluate one exact dataset category

```powershell
python -m app.tests.evaluation.ragas_logic.run_evals --category "Happy Path / Engineering"

```
Run evaluation tests via parametrization:

```powershell
python -m pytest app\tests\evaluation\test_agent.py -v

```

## Evaluation reports

Each evaluation run writes a timestamped directory:

```text
results/<UTC timestamp>/
├── results.json
├── results.csv
└── summary.md
```

Reports contain case status, evaluation mode, retrieved sources, deterministic checks, applicable RAGAS metrics, and estimated token usage and cost. The token and cost values are simplified local estimates, not authoritative OpenAI billing records.

## Troubleshooting

### `ModuleNotFoundError`

Activate the correct virtual environment and reinstall the dependencies:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### `OPENAI_API_KEY environment variable is not set`

Add the key to `.env` or set it in the same terminal session that launches Uvicorn, Pytest, or the evaluation command.

### PostgreSQL connection failure

Confirm Docker Desktop is running and inspect the database container:

```powershell
docker compose up -d
docker ps
```

Also confirm that port `5432` is not being used by another local PostgreSQL instance.

### Port 8000 is already in use

Start Uvicorn on another port:

```powershell
uvicorn app.main:app --reload --port 8080
```

Then open [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs).

## Stop the local database

Stop the container while preserving its Docker volume:

```powershell
docker compose down
```

Removing the `postgres_data` volume also removes the locally stored database data, so do that only when a full reset is intended.

## Clean cache

```powershell
Remove-Item -Recurse -Force .pytest_cache
```
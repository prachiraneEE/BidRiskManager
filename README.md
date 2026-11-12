# Bid Risk Manager

A FastAPI backend for managing bids and assessing their risk. Built as a practice project to demonstrate Python backend development and AI-infused product skills.

## Tech Stack

- **Python 3.12** with **uv** (package manager)
- **FastAPI** (web framework)
- **Pydantic** (request/response validation)
- **SQLite** + **SQLAlchemy** (database + ORM)
- **pytest** (testing)
- **Docker** (containerization)

## Project Structure

```
BidRiskManager/
├── app/
│   ├── main.py              # FastAPI app, middleware, startup
│   ├── config.py             # Settings from .env via pydantic-settings
│   ├── database.py           # SQLAlchemy engine and session
│   ├── logger.py             # Console + file logging
│   ├── models.py             # Client and Bid ORM models
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── routers/
│   │   ├── clients.py        # Client CRUD endpoints
│   │   └── bids.py           # Bid CRUD endpoints
│   └── services/
│       └── csv_import.py     # CSV data import logic
├── data/
│   ├── clients.csv           # 8 sample clients
│   └── bids.csv              # 18 sample bids (+ 3 bad rows for testing)
├── tests/
│   ├── conftest.py           # Test fixtures and DB setup
│   ├── test_clients.py       # Client endpoint tests
│   ├── test_bids.py          # Bid endpoint tests
│   ├── test_health.py        # Health check test
│   └── test_import.py        # CSV import tests
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Run Locally

```bash
# Clone the repo
git clone https://github.com/prachiraneEE/BidRiskManager.git
cd BidRiskManager

# Install dependencies
uv sync

# Create a .env file (optional — defaults work fine)
echo 'APP_NAME=bid-risk-manager
DATABASE_URL=sqlite:///./bid_risk_manager.db
LOG_LEVEL=INFO' > .env

# Start the server
uv run uvicorn app.main:app --reload --port 8000
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for the Swagger UI.

### Run with Docker

```bash
docker build -t bid-risk-manager .
docker run -p 8000:8000 bid-risk-manager
```

### Run Tests

```bash
uv run pytest -v
```

## API Endpoints

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

### Clients

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/clients/` | Create a client |
| GET | `/clients/` | List all clients |
| GET | `/clients/{id}` | Get a client by ID |
| PUT | `/clients/{id}` | Update a client |
| DELETE | `/clients/{id}` | Delete a client |

### Bids

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/bids/` | Create a bid |
| GET | `/bids/` | List bids (filter by `?status=` and `?client_id=`) |
| GET | `/bids/{id}` | Get a bid by ID |
| PUT | `/bids/{id}` | Update a bid |
| DELETE | `/bids/{id}` | Delete a bid |

### Data Import

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/import` | Import sample data from CSV files |

## Data Model

### Client

| Field | Type | Description |
|-------|------|-------------|
| id | int | Primary key |
| name | string | Client name |
| industry | string | Industry sector |
| past_bids_won | int | Number of past bids won |
| past_bids_lost | int | Number of past bids lost |

### Bid

| Field | Type | Description |
|-------|------|-------------|
| id | int | Primary key |
| client_id | int | Foreign key to Client |
| title | string | Bid title |
| value | float | Bid value (must be > 0) |
| estimated_cost | float | Estimated cost (must be > 0) |
| deadline | date | Bid deadline |
| status | enum | draft, submitted, won, or lost |
| notes | string | Optional notes |

## Validation

All endpoints validate input via Pydantic schemas:

- **Required fields** — missing `name`, `title`, etc. returns `422`
- **Positive values** — `value` and `estimated_cost` must be greater than 0
- **Valid status** — only `draft`, `submitted`, `won`, or `lost` accepted
- **Non-empty strings** — empty `name` or `title` rejected
- **Unknown resources** — missing client/bid returns `404`
- **Consistent errors** — all errors return JSON with a `detail` field

## Sample Data

The `POST /import` endpoint loads sample data from `data/clients.csv` and `data/bids.csv`:

- **8 clients** across industries (Technology, Finance, Healthcare, etc.)
- **18 bids** with varying risk profiles — some with thin margins, tight deadlines, or clients with poor track records
- **3 intentionally bad rows** to demonstrate error handling
- **Idempotent** — running the import twice creates no duplicates

## Phase 2 (Planned)

Phase 2 will add an AI-powered risk assessment agent using LangChain and an LLM via OpenRouter. The agent will evaluate bids on three risk signals:

- Profit margin below 15%
- Deadline less than 7 days away
- Client with 2+ previously lost bids

# SUCA API

FastAPI-based Japanese dictionary and flashcard management system with intelligent bilingual search, JWT authentication, FSRS spaced repetition, and optimized PostgreSQL database.

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.118-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![FSRS](https://img.shields.io/badge/FSRS-v6.3.0-brightgreen.svg)](https://github.com/open-spaced-repetition/fsrs-rs)

## Features

✨ **Japanese Dictionary Search**
- 180,000+ JMdict entries with kanji, readings, and definitions
- Intelligent bilingual search (auto-detects Japanese/English)
- Smart ranking: common words prioritized, exact matches first
- JLPT level tagging and word frequency data

🃏 **Smart Flashcard System**
- FSRS (Free Spaced Repetition Scheduler) v6.3.0 integration
- Adaptive review scheduling based on memory science
- Track difficulty, stability, and retrievability per card
- Multi-deck organization with due card statistics

🔐 **Secure Authentication**
- JWT-based authentication with refresh tokens
- bcrypt password hashing
- User isolation for personal flashcard data

⚡ **Production-Ready**
- Docker deployment with PostgreSQL 16
- Comprehensive test suite (60+ tests)
- Type-safe with mypy and Pydantic
- Auto-generated API documentation (OpenAPI/Swagger)

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Development Setup](#development-setup)
- [Docker Deployment](#docker-deployment)
- [API Reference](#api-reference)
- [Database Management](#database-management)
- [Testing](#testing)
- [Performance Optimization](#performance-optimization)
- [CI/CD Pipeline](#cicd-pipeline)

---

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/SUCA-Team/SUCA-api.git
cd SUCA-api
make docker-dev  # Builds, migrates, and starts all services

# Import dictionary data (REQUIRED)
make docker-db-restore FILE=dump.sql
```

**Access:**
- API Documentation: http://localhost:8000/docs
- Database: localhost:5433 (suca/suca)
- Health Check: http://localhost:8000/api/v1/health

**⚠️ Important:** The `dump.sql` file contains the JMdict Japanese dictionary data and is **required** for search functionality. Place it in the project root directory before running the import command.

### Local Development

```bash
poetry install
cp .env.example .env
# Edit .env with database credentials
poetry run alembic upgrade head

# Import dictionary data (REQUIRED)
psql -U postgres -d jmdict < dump.sql

make run
```

**⚠️ Important:** The `dump.sql` file contains the JMdict Japanese dictionary data and is **required** for search functionality.

---

## Architecture

### Stack

- **Framework**: FastAPI 0.118 (async ASGI)
- **ORM**: SQLModel (SQLAlchemy 2.0 + Pydantic)
- **Database**: PostgreSQL 16
- **Authentication**: JWT with bcrypt password hashing
- **Spaced Repetition**: FSRS (Free Spaced Repetition Scheduler) v6.3.0
- **Testing**: pytest with async support
- **Code Quality**: ruff (linting + formatting), mypy (type checking)
- **Containerization**: Docker + Docker Compose

### Project Structure

```
src/suca/
├── api/v1/endpoints/     # HTTP request handlers
│   ├── auth.py           # JWT authentication (register, login, me)
│   ├── flashcard.py      # CRUD for decks and cards with FSRS
│   ├── search.py         # Bilingual dictionary search
│   └── health.py         # Health check endpoint
├── core/                 # Configuration and middleware
│   ├── config.py         # Pydantic settings management
│   ├── auth.py           # JWT token creation/validation
│   ├── exceptions.py     # Custom exception classes
│   └── middleware.py     # Exception handlers and CORS
├── db/                   # Database layer
│   ├── db.py             # Engine creation with lazy initialization
│   ├── model.py          # SQLModel table definitions
│   └── base.py           # Base model with timestamps
├── services/             # Business logic layer
│   ├── search_service.py # Search algorithms and query optimization
│   ├── flashcard_service.py # Flashcard CRUD with FSRS integration
│   └── fsrs_service.py   # FSRS spaced repetition wrapper
├── schemas/              # Pydantic request/response models
└── main.py               # FastAPI application factory
```

### Design Patterns

**Layered Architecture:**
```
API Layer (FastAPI routes)
    ↓
Service Layer (Business logic)
    ↓
Database Layer (SQLModel/SQLAlchemy)
```

**Dependency Injection:**
```python
# Database session injection
def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session

# Service injection
@router.get("/search")
def search(session: Session = Depends(get_session)):
    service = SearchService(session)
    return service.search_entries(...)
```

**Lazy Initialization Pattern:**
```python
# src/suca/db/db.py
_engine: Engine | None = None

def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_database_engine(settings.database_url)
    return _engine
```

Benefits:
- Single database connection pool across application
- Test isolation via `set_engine()` override
- No environment variable flags needed

---

## Development Setup

### Prerequisites

- Python 3.11+ (3.13 recommended)
- PostgreSQL 16+
- Poetry 2.2+

### Installation

```bash
# 1. Install dependencies
poetry install

# 2. Configure environment
cp .env.example .env
```

**Required `.env` variables:**
```bash
# Database (PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASS=postgres
DB_NAME=jmdict

# JWT Authentication
JWT_SECRET_KEY=$(openssl rand -hex 32)  # Generate secure key

# Optional
DEBUG=true                              # Enable debug mode
SQLALCHEMY_ECHO=false                   # Log SQL queries
```

```bash
# 3. Create database
createdb jmdict

# 4. Run migrations
poetry run alembic upgrade head

# 5. Import dictionary data (REQUIRED)
psql -U postgres -d jmdict < dump.sql
# This imports the JMdict Japanese-English dictionary data

# 6. (Optional) Load sample flashcard data
poetry run python scripts/create_sample_data.py
```

### Dictionary Data (dump.sql)

**⚠️ REQUIRED:** The application requires Japanese dictionary data to function.

**What is dump.sql?**
- Contains JMdict Japanese-English dictionary entries
- Includes ~180,000+ dictionary entries with kanji, readings, and definitions
- Pre-populated tables: `entry`, `kanji`, `reading`, `sense`, `gloss`, `example`

**Obtaining the data:**

1. **From project maintainers** (recommended):
   ```bash
   # Contact the SUCA team for the dump.sql file
   # Place it in the project root directory
   ```

2. **Generate from JMdict XML** (advanced):
   ```bash
   # Download JMdict from: http://www.edrdg.org/jmdict/j_jmdict.html
   # Parse using provided script
   poetry run python scripts/parse_jmdict.py
   # Export to SQL
   pg_dump -U postgres -d jmdict > dump.sql
   ```

**Import instructions:**

**Local PostgreSQL:**
```bash
# Import to local database
psql -U postgres -d jmdict < dump.sql

# Verify import
psql -U postgres -d jmdict -c "SELECT COUNT(*) FROM entry;"
# Expected output: ~180,000+ entries
```

**Docker:**
```bash
# Import to Docker database
make docker-db-restore FILE=dump.sql
# or
cat dump.sql | docker-compose exec -T db psql -U suca -d jmdict

# Verify import
make docker-db-shell
# Then: SELECT COUNT(*) FROM entry;
```

**File location:**
```
SUCA-api/
├── dump.sql          ← Place dictionary data here
├── src/
├── tests/
└── ...
```

**Without dictionary data:**
- ❌ Search endpoints will return empty results
- ❌ `/api/v1/search` will not find any words
- ✅ Authentication and flashcard features still work

### Running the Application

**Development (auto-reload):**
```bash
make run
# or
poetry run uvicorn src.suca.main:app --reload --port 8000
```

**Production:**
```bash
make run-prod
# or
poetry run uvicorn src.suca.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Available Make Commands

```bash
# Development
make run                # Development server with hot-reload
make run-prod           # Production server (multi-worker)
make shell              # Open poetry shell

# Code Quality
make lint               # Check code style with ruff
make lint-fix           # Auto-fix linting issues
make format             # Format code with ruff
make type-check         # Run mypy type checking
make all-checks         # Run all quality checks + tests

# Testing
make test               # Run all tests
make test-cov           # Run tests with coverage report
make test-file FILE=tests/test_auth.py  # Run specific test file

# Database
make migrate MSG="description"  # Create new migration
make db-upgrade         # Apply migrations
make db-downgrade       # Rollback one migration
make db-reset           # Reset database (WARNING: destroys data)
make db-history         # Show migration history

# Cleanup
make clean              # Remove cache files
make clean-all          # Deep clean including Poetry cache
```

---

## Docker Deployment

### Architecture

```
┌─────────────────┐      ┌──────────────────┐
│  API Container  │─────▶│  PostgreSQL 16   │
│  (FastAPI)      │      │  (postgres_data) │
└─────────────────┘      └──────────────────┘
        │
        │ (optional)
        ▼
┌─────────────────┐
│    pgAdmin 4    │
│  (DB Management)│
└─────────────────┘
```

### Docker Compose Services

**Development (`docker-compose.yml`):**
- `db` - PostgreSQL 16 with persistent volume
- `api` - FastAPI app with hot-reload (source mounted)
- `pgadmin` - Database GUI (profile: `tools`)

**Production (`docker-compose.prod.yml`):**
- Optimized multi-stage builds
- No volume mounts (baked-in code)
- Health checks configured
- Resource limits defined

### Essential Commands

```bash
# Development
make docker-dev         # Build + migrate + start (one command)
make docker-up          # Start services
make docker-down        # Stop services
make docker-logs        # Tail all logs
make docker-logs-api    # API logs only
make docker-shell       # Shell into API container
make docker-python      # Python REPL in container

# Database
make docker-migrate     # Run migrations in Docker
make docker-migrate-create MSG="add indexes"  # Create migration
make docker-db-shell    # PostgreSQL shell (psql)
make docker-db-backup   # Export database to SQL file
make docker-db-restore FILE=dump.sql  # Import SQL file

# Testing in Docker
make docker-test        # Run pytest in container
make docker-test-cov    # Generate coverage report
make docker-lint        # Run ruff checks
make docker-format      # Format code

# Production
make docker-prod-up     # Start production stack
make docker-prod-build  # Build production images
make docker-prod-logs   # View production logs

# Maintenance
make docker-rebuild     # Rebuild from scratch (no cache)
make docker-clean       # Remove stopped containers
make docker-clean-all   # Nuclear option (removes everything)
```

### Environment Configuration

**`.env` for Docker:**
```bash
# Database (Docker service name)
DB_HOST=db              # Container hostname
DB_PORT=5433            # External port (mapped from internal 5432)
DB_USER=suca
DB_PASS=suca
DB_NAME=jmdict

# Application
ENV=dev
DEBUG=true
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Performance
SQLALCHEMY_ECHO=false   # Set true to debug SQL queries
```

### Volume Mounts (Development)

```yaml
# docker-compose.yml
volumes:
  - ./src:/app/src              # Hot-reload source code
  - ./tests:/app/tests          # Test files
  - ./scripts:/app/scripts      # Utility scripts
  - ./alembic:/app/alembic      # Migrations
  - postgres_data:/var/lib/postgresql/data  # Persistent database
```

### Dockerfile Architecture

**Development (`Dockerfile.dev`):**
```dockerfile
FROM python:3.13-slim
RUN pip install poetry==2.2.1
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install  # Includes dev dependencies
COPY . .
CMD ["poetry", "run", "uvicorn", "src.suca.main:app", "--reload", "--host", "0.0.0.0"]
```

**Production (`Dockerfile`):**
```dockerfile
# Multi-stage build
FROM python:3.13-slim AS builder
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.13-slim
COPY --from=builder requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
WORKDIR /app
USER nobody
CMD ["uvicorn", "src.suca.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Data Import/Export

**Import dictionary data (REQUIRED for search functionality):**
```bash
# Docker import
make docker-db-restore FILE=dump.sql

# Verify import
make docker-db-shell
# Then in psql: SELECT COUNT(*) FROM entry;
# Expected: ~180,000+ entries
```

**Export from local PostgreSQL:**
```bash
pg_dump -U postgres -h localhost -p 5432 -d suca --no-owner --no-acl > dump.sql
```

**Import to Docker:**
```bash
cat dump.sql | docker-compose exec -T db psql -U suca -d jmdict
# or
make docker-db-restore FILE=dump.sql
```

**Backup Docker database:**
```bash
make docker-db-backup
# Creates: backup_YYYYMMDD_HHMMSS.sql
```

**⚠️ Note:** The `dump.sql` file containing JMdict dictionary data must be placed in the project root directory. Without this data, search endpoints will return empty results.

### Troubleshooting

**Port conflict (5432 in use):**
```bash
# .env already configured for 5433
DB_PORT=5433
```

**Migrations out of sync:**
```bash
# Mark database as up-to-date with current schema
docker-compose exec api poetry run alembic stamp head

# Then create new migration
make docker-migrate-create MSG="your changes"
```

**Fresh start:**
```bash
make docker-fresh  # Stops, removes volumes, rebuilds, migrates
```

**View container resource usage:**
```bash
docker stats
# or
make docker-stats
```

---

## API Reference

### Authentication

All flashcard endpoints require JWT authentication. Health and search endpoints are public.

**Register User:**
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "SecurePass123"
}

Response: 201 Created
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Login:**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "SecurePass123"
}

Response: 200 OK
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Get Current User:**
```http
GET /api/v1/auth/me
Authorization: Bearer <token>

Response: 200 OK
{
  "username": "testuser",
  "email": "test@example.com"
}
```

### Dictionary Search

Intelligent bilingual search with auto-language detection.

**Search (Japanese or English):**
```http
GET /api/v1/search?q=食べる&limit=10&include_rare=false

Response: 200 OK
{
  "results": [
    {
      "word": "食べる",
      "reading": "たべる",
      "is_common": true,
      "jlpt_level": "N5",
      "meanings": [
        {
          "pos": ["Ichidan verb", "transitive verb"],
          "definitions": ["to eat"],
          "examples": [],
          "notes": []
        }
      ],
      "other_forms": ["喰べる"],
      "tags": ["common word"],
      "variants": [
        {"kanji": "食べる", "reading": "たべる"}
      ]
    }
  ],
  "total_count": 1,
  "query": "食べる",
  "message": "Found 1 results for '食べる' (Japanese search)"
}
```

**Query Parameters:**
- `q` (required) - Search term (auto-detects Japanese/English)
- `limit` (optional, default: 10, max: 100) - Results per page
- `include_rare` (optional, default: false) - Include uncommon words
- `page` (optional, default: 1) - Page number

**Language Detection:**
- ASCII characters → English search (searches glosses)
- Japanese characters → Japanese search (searches kanji/readings)

**Search Prioritization:**

Two-dimensional ranking system:
1. Common words always ranked above rare words (+10,000 priority)
2. Within each group, ranked by match type:

| Match Type | Common Score | Rare Score |
|------------|--------------|------------|
| Exact match | 11,000 | 1,000 |
| Starts with | 10,500 | 500 |
| Contains (word boundary) | 10,300 | 300 |
| Contains (anywhere) | 10,100 | 100 |

**Search Suggestions:**
```http
GET /api/v1/suggestions?q=食&limit=10

Response: 200 OK
{
  "suggestions": ["食べる", "食事", "食物", "食料品", ...]
}
```

### Flashcard Management with FSRS

SUCA uses **FSRS (Free Spaced Repetition Scheduler)** v6.3.0 for intelligent flashcard scheduling based on spaced repetition science.

**What is FSRS?**

FSRS is a modern spaced repetition algorithm that optimizes review intervals based on:
- **Difficulty**: How hard the card is to remember
- **Stability**: How long the memory lasts
- **Retrievability**: Current probability of recall
- **Review history**: Your actual performance over time

Unlike traditional SM-2 algorithms, FSRS uses a sophisticated memory model that adapts to your learning patterns.

**Card States:**
- **New (0)**: Never reviewed
- **Learning (1)**: Initial learning phase
- **Review (2)**: In long-term memory
- **Relearning (3)**: Forgotten and relearning

**Rating System:**
```
1 = Again    - Completely forgot
2 = Hard     - Difficult to recall
3 = Good     - Recalled correctly
4 = Easy     - Recalled effortlessly
```

**List Decks:**
```http
GET /api/v1/flashcard/decks
Authorization: Bearer <token>

Response: 200 OK
{
  "decks": [
    {
      "id": 1,
      "user_id": "testuser",
      "name": "JLPT N5 Vocabulary",
      "flashcard_count": 25,
      "created_at": "2025-12-04T10:00:00Z",
      "updated_at": "2025-12-04T10:00:00Z"
    }
  ],
  "total_count": 1
}
```

**Create Deck:**
```http
POST /api/v1/flashcard/decks
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "JLPT N5 Vocabulary"
}

Response: 201 Created
{
  "id": 1,
  "user_id": "testuser",
  "name": "JLPT N5 Vocabulary",
  "flashcard_count": 0,
  "created_at": "2025-12-04T10:00:00Z",
  "updated_at": "2025-12-04T10:00:00Z"
}
```

**Add Card to Deck:**
```http
POST /api/v1/flashcard/decks/1/cards
Authorization: Bearer <token>
Content-Type: application/json

{
  "front": "食べる",
  "back": "to eat"
}

Response: 201 Created
{
  "id": 1,
  "deck_id": 1,
  "user_id": "testuser",
  "front": "食べる",
  "back": "to eat",
  "difficulty": 0.0,
  "stability": 0.0,
  "reps": 0,
  "state": 0,
  "last_review": null,
  "due": "2025-12-04T10:05:00Z",
  "created_at": "2025-12-04T10:05:00Z",
  "updated_at": "2025-12-04T10:05:00Z"
}
```

**Review Card (FSRS):**
```http
POST /api/v1/flashcard/decks/1/cards/1/review
Authorization: Bearer <token>
Content-Type: application/json

{
  "rating": 3
}

Response: 200 OK
{
  "id": 1,
  "deck_id": 1,
  "user_id": "testuser",
  "front": "食べる",
  "back": "to eat",
  "difficulty": 5.42,
  "stability": 2.31,
  "reps": 1,
  "state": 1,
  "last_review": "2025-12-04T10:10:00Z",
  "due": "2025-12-06T14:25:00Z",
  "retrievability": 0.95,
  "created_at": "2025-12-04T10:05:00Z",
  "updated_at": "2025-12-04T10:10:00Z"
}
```

**FSRS Fields Explained:**
- `difficulty`: Card difficulty (higher = harder)
- `stability`: Memory retention in days
- `reps`: Number of reviews (maps to FSRS `step`)
- `state`: Card state (0=New, 1=Learning, 2=Review, 3=Relearning)
- `last_review`: When last reviewed
- `due`: Next review scheduled time
- `retrievability`: Current recall probability (0-1)

**Get Due Cards:**
```http
GET /api/v1/flashcard/due
Authorization: Bearer <token>

Response: 200 OK
{
  "decks": [
    {
      "deck_id": 1,
      "deck_name": "JLPT N5 Vocabulary",
      "total_cards": 25,
      "new_cards": 10,
      "learning_cards": 5,
      "review_cards": 10,
      "due_cards": 8
    }
  ],
  "total_due": 8
}
```

**Update Card:**
```http
PUT /api/v1/flashcard/decks/1/cards/1
Authorization: Bearer <token>
Content-Type: application/json

{
  "back": "to eat; to consume"
}

Response: 200 OK
{...}
```

**Delete Card:**
```http
DELETE /api/v1/flashcard/decks/1/cards/1
Authorization: Bearer <token>

Response: 204 No Content
```

### Health Check

```http
GET /api/v1/health

Response: 200 OK
{
  "success": true,
  "message": "API is healthy",
  "data": {
    "status": "healthy",
    "timestamp": "2025-12-04T12:00:00Z",
    "version": "1.0.0",
    "database_status": "healthy",
    "uptime": 3600.5
  }
}
```

---

## Database Management

### Schema Overview

**Dictionary Tables:**
- `entry` - Main dictionary entries (ent_seq PK, is_common, jlpt_level)
- `kanji` - Kanji forms (keb, entry_id FK)
- `reading` - Readings (reb, entry_id FK)
- `sense` - Word senses/meanings (entry_id FK)
- `gloss` - Definitions (text, lang, sense_id FK)
- `example` - Usage examples (text, sense_id FK)

**Flashcard Tables:**
- `flashcard_decks` - User decks (user_id, name)
- `flashcards` - Cards (deck_id FK, user_id, front, back)

### Migrations with Alembic

**Create migration from model changes:**
```bash
# Auto-generate migration
make migrate MSG="add user table"
# or
poetry run alembic revision --autogenerate -m "add user table"

# Review generated file in alembic/versions/
# Edit if needed, then apply:
make db-upgrade
```

**Create empty migration for custom SQL:**
```bash
poetry run alembic revision -m "add custom indexes"
# Edit generated file to add custom SQL
make db-upgrade
```

**Common operations:**
```bash
make db-upgrade      # Apply all pending migrations
make db-downgrade    # Rollback one migration
make db-history      # View migration history
make db-current      # Show current version
make db-reset        # Downgrade to base, then upgrade to head (DANGER)
```

**Docker migrations:**
```bash
# Apply all pending migrations
make docker-migrate

# Create a new migration from model changes
make docker-migrate-create MSG="add new table"
# or
docker-compose exec api poetry run alembic revision --autogenerate -m "add new table"

# View migration history
docker-compose exec api poetry run alembic history

# Check current version
docker-compose exec api poetry run alembic current

# Manual migration creation (for custom SQL)
docker-compose exec api poetry run alembic revision -m "custom changes"
```

**⚠️ Important for Team Development:**
- The `alembic/versions/` directory is mounted as a volume in Docker
- Migration files created in the container are immediately visible on your host machine
- Your team can commit migration files to Git and others will see them automatically
- No need to rebuild Docker images when adding new migrations
- Always run `make docker-migrate` after pulling new migrations from Git

### Performance Indexes

Optimized indexes for fast search queries:

**Entry table:**
- `ix_entry_jlpt_level` (jlpt_level) - JLPT level filtering

**Kanji table:**
- `ix_kanji_keb` (keb) - Japanese text search with LIKE
- `ix_kanji_entry_id` (entry_id) - JOIN optimization

**Reading table:**
- `ix_reading_reb` (reb) - Hiragana/katakana search
- `ix_reading_entry_id` (entry_id) - JOIN optimization

**Gloss table:**
- `ix_gloss_text` (text) - English definition search
- `ix_gloss_lang` (lang) - Language filtering
- `ix_gloss_sense_id` (sense_id) - JOIN optimization

**Other indexes:**
- `ix_sense_entry_id`, `ix_example_sense_id`
- `ix_flashcard_decks_user_id`, `ix_flashcards_deck_id`, `ix_flashcards_user_id`

**Verify indexes:**
```sql
-- Via psql
\d kanji

-- Or via Docker
docker-compose exec db psql -U suca -d jmdict -c "\d kanji"
```

**Index performance impact:**
- 10-100x faster LIKE queries on indexed columns
- Efficient JOINs across tables
- Optimized sorting by word length and priority

---

## Testing

### Test Architecture

```
tests/
├── conftest.py           # Fixtures (session, client, auth)
├── test_auth.py          # JWT authentication tests
├── test_flashcard.py     # Flashcard CRUD tests
├── test_health.py        # Health endpoint tests
└── test_search.py        # Search functionality tests
```

### Key Fixtures

**`session`** - SQLite in-memory database:
```python
@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    set_engine(engine)  # Override global engine
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
```

**`client`** - Unauthenticated test client:
```python
@pytest.fixture
def client(session: Session) -> TestClient:
    def override_get_session():
        yield session
    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)
```

**`auth_client`** - Authenticated test client:
```python
@pytest.fixture
def auth_client(client: TestClient, auth_headers: dict) -> TestClient:
    client.headers.update(auth_headers)
    return client
```

### Running Tests

```bash
# All tests
make test
poetry run pytest

# With coverage
make test-cov
poetry run pytest --cov=src/suca --cov-report=html

# Specific file
make test-file FILE=tests/test_auth.py
poetry run pytest tests/test_auth.py -v

# Specific test
poetry run pytest tests/test_auth.py::test_login_success -v

# Watch mode (requires pytest-watch)
poetry run ptw

# In Docker
make docker-test
make docker-test-cov
```

### Test Examples

**Testing authenticated endpoints:**
```python
def test_create_deck(auth_client: TestClient):
    response = auth_client.post(
        "/api/v1/flashcard/decks",
        json={"name": "Test Deck"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Deck"
```

**Testing search functionality:**
```python
def test_search_japanese(client: TestClient):
    response = client.get("/api/v1/search?q=行く")
    assert response.status_code == 200
    assert response.json()["total_count"] > 0
```

### Coverage Requirements

- Maintain >80% code coverage
- All new features must include tests
- Tests should be isolated and deterministic

---

## Performance Optimization

### Database Query Optimization

**1. Indexed Columns**

All search columns have B-tree indexes:
```sql
CREATE INDEX ix_kanji_keb ON kanji(keb);
CREATE INDEX ix_gloss_text ON gloss(text);
CREATE INDEX ix_entry_is_common ON entry(is_common);
```

**2. Efficient JOIN Strategy**

```python
# Bad: N+1 queries
for entry in entries:
    kanjis = session.query(Kanji).filter_by(entry_id=entry.id).all()

# Good: Single query with JOIN
stmt = (
    select(Entry, Kanji)
    .join(Kanji, Entry.ent_seq == Kanji.entry_id)
    .where(Kanji.keb.like("%食%"))
)
```

**3. Query Result Limiting**

```python
# Limit results early in database
stmt = stmt.limit(request.limit * 2)  # Get extras for deduplication

# Deduplicate in Python (faster than DISTINCT in DB for complex queries)
seen = set()
unique_ids = [id for id, _, _ in results if id not in seen and not seen.add(id)]
```

**4. Lazy Loading vs Eager Loading**

```python
# SQLModel relationships are lazy by default
entry.kanjis  # Triggers separate query

# For bulk operations, prefetch relationships:
stmt = select(Entry).options(joinedload(Entry.kanjis))
```

### Application Performance

**Connection Pooling:**
```python
# src/suca/db/db.py
engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=5,          # Max connections
    max_overflow=10,      # Burst capacity
    pool_pre_ping=True,   # Verify connections before use
)
```

**Async Considerations:**
- FastAPI endpoints are async-compatible
- Database operations use sync SQLAlchemy (via SQLModel)
- For high concurrency, consider:
  - `asyncpg` + SQLAlchemy async engine
  - Connection pool tuning
  - Read replicas for search queries

**Caching Strategy:**
```python
# Future enhancement: Add Redis for search result caching
@cache(ttl=3600)
def search_entries(query: str):
    # Expensive database query
    pass
```

### Benchmarking

**Query performance:**
```sql
-- Enable query timing
\timing

-- Analyze query plan
EXPLAIN ANALYZE
SELECT * FROM entry
JOIN kanji ON entry.ent_seq = kanji.entry_id
WHERE kanji.keb LIKE '食%'
LIMIT 10;
```

**Application profiling:**
```bash
# Install profiling tools
poetry add --group dev py-spy

# Profile running application
py-spy top --pid <process_id>

# Generate flamegraph
py-spy record -o profile.svg -- python -m uvicorn src.suca.main:app
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

**1. CI Pipeline (`.github/workflows/ci.yml`)**

Triggers: Push to `main`/`develop`, Pull Requests

Jobs:
- **Lint** - ruff check for code style
- **Type Check** - mypy static analysis (non-blocking)
- **Test** - pytest with PostgreSQL service container
  - Python 3.11, 3.12, 3.13 matrix
  - Coverage reporting to Codecov
- **Security** - Bandit security scanning
- **Build** - Poetry package build validation
- **Docker** - Multi-platform image build test

**2. Release Workflow (`.github/workflows/release.yml`)**

Triggers: Version tags (`v*.*.*`)

Actions:
- Build Poetry package
- Create GitHub Release with artifacts
- Publish Docker image to Docker Hub

**3. CodeQL Analysis (`.github/workflows/codeql.yml`)**

Triggers: Push to `main`, Weekly schedule

- Advanced security vulnerability scanning
- Results in GitHub Security tab

**4. Dependency Updates (`.github/workflows/dependency-update.yml`)**

Triggers: Weekly (Monday 9 AM UTC)

- Checks for outdated dependencies
- Creates PR with updates

### Running CI Locally

**Pre-commit checks:**
```bash
make ci-checks
# Runs: format-check, lint, type-check, test
```

**Full CI simulation:**
```bash
# Lint
make lint

# Type check
make type-check

# Test with PostgreSQL
createdb test_jmdict
DB_NAME=test_jmdict make test-cov

# Security scan
poetry run bandit -r src/

# Build package
poetry build
```

### Release Process

1. Update version in `pyproject.toml`:
```toml
[tool.poetry]
version = "1.0.0"
```

2. Commit and tag:
```bash
git add pyproject.toml
git commit -m "chore: bump version to 1.0.0"
git tag v1.0.0
git push origin main --tags
```

3. GitHub Actions automatically:
   - Runs full CI pipeline
   - Builds package
   - Creates GitHub Release
   - Publishes Docker image

### Required Secrets

Configure in GitHub Settings → Secrets:

| Secret | Purpose |
|--------|---------|
| `CODECOV_TOKEN` | Upload coverage reports |
| `DOCKER_HUB_USERNAME` | Publish Docker images |
| `DOCKER_HUB_TOKEN` | Docker Hub authentication |

---

## Contributing

### Development Workflow

1. **Fork and clone:**
```bash
git clone https://github.com/YOUR_USERNAME/SUCA-api.git
cd SUCA-api
git remote add upstream https://github.com/SUCA-Team/SUCA-api.git
```

2. **Create feature branch:**
```bash
git checkout -b feature/intelligent-caching
```

3. **Make changes with tests:**
```bash
# Write code
vim src/suca/services/cache_service.py

# Write tests
vim tests/test_cache.py

# Run checks
make all-checks
```

4. **Commit with conventional commits:**
```bash
git commit -m "feat: add Redis caching for search results"
```

Commit types:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `refactor:` Code restructuring
- `test:` Adding tests
- `chore:` Tooling/config changes

5. **Push and create PR:**
```bash
git push origin feature/intelligent-caching
# Open pull request on GitHub
```

### Code Quality Standards

**Type hints required:**
```python
def search_entries(
    self,
    query: str,
    limit: int = 10
) -> list[DictionaryEntryResponse]:
    ...
```

**Docstrings for public APIs:**
```python
def create_flashcard(self, deck_id: int, data: FlashcardCreate) -> Flashcard:
    """
    Create a new flashcard in the specified deck.

    Args:
        deck_id: ID of the target deck
        data: Flashcard content (front/back)

    Returns:
        Created flashcard instance

    Raises:
        NotFoundException: Deck not found
        ValidationException: Invalid flashcard data
    """
    ...
```

**Test coverage:**
- All new features must include tests
- Aim for >80% coverage
- Use fixtures for common setups

---

## License

MIT License - see [LICENSE](LICENSE) file.

## Support

- **Issues**: [GitHub Issues](https://github.com/SUCA-Team/SUCA-api/issues)
- **Documentation**: http://localhost:8000/docs
- **Repository**: https://github.com/SUCA-Team/SUCA-api

---

**Built with FastAPI, SQLModel, and PostgreSQL**

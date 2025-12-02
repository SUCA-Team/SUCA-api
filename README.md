# SUCA API

A modern Japanese dictionary API with flashcard management, built with FastAPI. Features intelligent search, JWT authentication, and comprehensive language learning tools.

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.118-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

---

## 🚀 Features

### Core Functionality
- ✅ **Intelligent Dictionary Search** - Prioritized search with exact matches, common words, and partial matches
- 🗂️ **Flashcard Management** - Create decks and cards for language learning with user isolation
- 🔐 **JWT Authentication** - Secure token-based authentication with rate limiting
- 💾 **PostgreSQL Database** - Reliable data persistence with Alembic migrations
- 🏥 **Health Monitoring** - Comprehensive health checks with database status

### Technical Features
- 🎯 **Type Safety** - Full type hints with Pydantic models and SQLModel
- 🧪 **Comprehensive Testing** - Test coverage with pytest fixtures and authenticated clients
- 📝 **Structured Logging** - Detailed logging for debugging and monitoring
- 🛡️ **Error Handling** - Structured error responses with proper HTTP status codes
- 🌐 **CORS Support** - Configured for frontend integration
- 📊 **API Documentation** - Auto-generated Swagger UI and ReDoc

---

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Installation](#️-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [Authentication](#-authentication)
- [API Endpoints](#-api-endpoints)
- [Testing](#-testing)
- [Database Operations](#️-database-operations)
- [Development](#-development)
- [Deployment](#-deployment)
- [Architecture](#️-architecture)
- [Contributing](#-contributing)

---

## ⚡ Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/SUCA-api.git
cd SUCA-api

# Install dependencies
poetry install

# Set up environment
cp .env.example .env
# Edit .env with your database credentials

# Run database migrations
poetry run alembic upgrade head

# Start the server
poetry run uvicorn src.suca.main:app --reload

# Open your browser
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

---

## 📁 Project Structure

```
SUCA-api/
├── src/suca/
│   ├── api/                    # API layer
│   │   ├── deps.py            # Dependency injection
│   │   └── v1/                # API version 1
│   │       ├── router.py      # Main API router
│   │       └── endpoints/     # API endpoints
│   │           ├── auth.py    # Authentication endpoints
│   │           ├── flashcard.py # Flashcard CRUD
│   │           ├── health.py  # Health checks
│   │           └── search.py  # Dictionary search
│   ├── core/                  # Core configuration
│   │   ├── auth.py           # JWT authentication logic
│   │   ├── config.py         # Application settings
│   │   ├── exceptions.py     # Custom exceptions
│   │   ├── middleware.py     # Exception handlers
│   │   └── validators.py     # Environment validation
│   ├── db/                   # Database layer
│   │   ├── base.py          # Base model classes
│   │   ├── db.py            # Database configuration
│   │   └── model.py         # SQLModel definitions
│   ├── schemas/             # Pydantic schemas
│   │   ├── base.py         # Base response models
│   │   ├── flashcard_schemas.py # Flashcard schemas
│   │   ├── health.py       # Health check schemas
│   │   └── search.py       # Search schemas
│   ├── services/           # Business logic layer
│   │   ├── base.py        # Base service class
│   │   ├── flashcard_service.py # Flashcard operations
│   │   └── search_service.py    # Search operations
│   ├── utils/             # Utility functions
│   │   ├── logging.py    # Logging utilities
│   │   └── text.py       # Text processing
│   └── main.py           # FastAPI application
├── tests/                # Test suite
│   ├── conftest.py      # Test fixtures
│   ├── test_auth.py     # Authentication tests
│   ├── test_flashcard.py # Flashcard tests
│   ├── test_health.py   # Health check tests
│   └── test_search.py   # Search tests
├── alembic/             # Database migrations
├── scripts/             # Utility scripts
├── .env.example         # Environment template
├── pyproject.toml       # Dependencies
├── Makefile            # Development commands
└── README.md           # This file
```

---

## 🛠️ Installation

### Prerequisites

- **Python 3.13+** - [Download](https://www.python.org/downloads/)
- **PostgreSQL 16+** - [Download](https://www.postgresql.org/download/)
- **Poetry** - [Install](https://python-poetry.org/docs/#installation)

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/SUCA-api.git
cd SUCA-api
```

### Step 2: Install Dependencies

```bash
# Install all dependencies
poetry install

# Or install only production dependencies
poetry install --only=main
```

### Step 3: Set Up Database

```bash
# Create PostgreSQL database
createdb jmdict

# Or using psql
psql -U postgres -c "CREATE DATABASE jmdict;"
```

### Step 4: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASS=your_password
DB_NAME=jmdict

# Application
DEBUG=true
API_TITLE=SUCA API
API_VERSION=1.0.0

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32
```

### Step 5: Run Migrations

```bash
poetry run alembic upgrade head
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DB_HOST` | PostgreSQL host | `localhost` | Yes |
| `DB_PORT` | PostgreSQL port | `5432` | Yes |
| `DB_USER` | Database user | `postgres` | Yes |
| `DB_PASS` | Database password | - | Yes |
| `DB_NAME` | Database name | `jmdict` | Yes |
| `JWT_SECRET_KEY` | Secret key for JWT | - | Yes (Production) |
| `DEBUG` | Enable debug mode | `false` | No |
| `API_TITLE` | API title | `SUCA API` | No |
| `API_VERSION` | API version | `1.0.0` | No |

### Generate JWT Secret Key

```bash
# Generate a secure random key
openssl rand -hex 32
```

---

## 🚦 Running the Application

### Development Mode

```bash
# Using Poetry
poetry run uvicorn src.suca.main:app --reload

# Using Make
make run
```

Server will start at: **http://localhost:8000**

### Production Mode

```bash
# Without auto-reload
poetry run uvicorn src.suca.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using Make
make run-prod
```

### Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

---

## 🔐 Authentication

The API uses **JWT (JSON Web Tokens)** for authentication.

### Quick Start with Authentication

#### 1. Register a New User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "myuser",
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### 2. Login (Get Token)

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "password": "password123"
  }'
```

#### 3. Use Token in Requests

```bash
# Get current user info
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Create a flashcard deck
curl -X POST http://localhost:8000/api/v1/flashcard/decks \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Japanese N5 Vocabulary"}'
```

### Demo Credentials

For testing, use these credentials:
- **Username**: `demo_user`
- **Password**: `password123`

### Using Swagger UI

1. Open http://localhost:8000/docs
2. Click `POST /api/v1/auth/login`
3. Click "Try it out"
4. Enter credentials and execute
5. Copy the `access_token` from response
6. Click the **"Authorize" 🔓** button (top right)
7. Paste token and click "Authorize"
8. Now you can test all protected endpoints! ✅

### Security Features

- ✅ **Password Hashing** - Bcrypt/Argon2 for secure storage
- ✅ **Rate Limiting** - Prevents brute-force attacks
  - Login: 5 attempts/minute
  - Register: 5 attempts/hour
- ✅ **Token Expiration** - Tokens expire after 30 minutes
- ✅ **User Isolation** - Users only see their own data
- ✅ **Validation** - Username (3-50 chars), Password (8-128 chars)

---

## 📡 API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/register` | Register new user | No |
| `POST` | `/login` | Login and get JWT token | No |
| `GET` | `/me` | Get current user info | Yes |

**Example: Register**
```bash
POST /api/v1/auth/register
{
  "username": "newuser",
  "email": "new@example.com",
  "password": "mypassword123"
}
```

**Example: Login**
```bash
POST /api/v1/auth/login
{
  "username": "demo_user",
  "password": "password123"
}
```

---

### Flashcard Management (`/api/v1/flashcard`)

All flashcard endpoints **require authentication**.

#### Deck Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/decks` | List all user's decks |
| `POST` | `/decks` | Create new deck |
| `GET` | `/decks/{deck_id}` | Get specific deck |
| `PUT` | `/decks/{deck_id}` | Update deck |
| `DELETE` | `/decks/{deck_id}` | Delete deck |

**Example: Create Deck**
```bash
POST /api/v1/flashcard/decks
Headers: Authorization: Bearer <token>
{
  "name": "Japanese N5 Vocabulary"
}
```

**Example: List Decks**
```bash
GET /api/v1/flashcard/decks
Headers: Authorization: Bearer <token>

Response:
{
  "decks": [
    {
      "id": 1,
      "user_id": "demo_user",
      "name": "Japanese N5 Vocabulary",
      "flashcard_count": 10,
      "created_at": "2025-12-02T10:00:00",
      "updated_at": "2025-12-02T10:00:00"
    }
  ],
  "total_count": 1,
  "success": true
}
```

#### Card Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/decks/{deck_id}/cards` | List all cards in deck |
| `POST` | `/decks/{deck_id}/cards` | Add card to deck |
| `GET` | `/decks/{deck_id}/cards/{card_id}` | Get specific card |
| `PUT` | `/decks/{deck_id}/cards/{card_id}` | Update card |
| `DELETE` | `/decks/{deck_id}/cards/{card_id}` | Delete card |

**Example: Add Card**
```bash
POST /api/v1/flashcard/decks/1/cards
Headers: Authorization: Bearer <token>
{
  "front": "行く",
  "back": "to go"
}
```

**Example: Update Card**
```bash
PUT /api/v1/flashcard/decks/1/cards/5
Headers: Authorization: Bearer <token>
{
  "back": "to go (verb)"
}
```

---

### Dictionary Search (`/api/v1/search`)

Search Japanese dictionary entries. **No authentication required**.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/search` | Search dictionary entries |

**Query Parameters:**
- `q` (required) - Search query
- `limit` (optional) - Max results (default: 10, max: 100)
- `include_rare` (optional) - Include rare words (default: false)

**Example: Search**
```bash
GET /api/v1/search?q=行く&limit=5

Response:
{
  "results": [
    {
      "word": "行く",
      "reading": "いく",
      "is_common": true,
      "jlpt_level": "N5",
      "meanings": [
        {
          "pos": ["verb"],
          "definitions": ["to go", "to move"],
          "examples": [],
          "notes": []
        }
      ],
      "other_forms": ["行く"],
      "tags": ["common word"],
      "variants": [
        {"kanji": "行く", "reading": "いく"}
      ]
    }
  ],
  "total_count": 1,
  "query": "行く",
  "success": true
}
```

**Search Prioritization:**
1. **Exact matches** - Query exactly matches word (行 = 行)
2. **Common words starting with query** - 行 → 行く, 行き
3. **Common words containing query** - 行 → 銀行, 旅行
4. **Other partial matches** - All other results

---

### Health Check (`/api/v1/health`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/health` | Application health status | No |

**Example:**
```bash
GET /api/v1/health

Response:
{
  "data": {
    "status": "healthy",
    "timestamp": "2025-12-02T15:30:00",
    "version": "1.0.0",
    "database_status": "healthy",
    "uptime": 3600.5
  },
  "success": true,
  "message": "API is healthy"
}
```

---

## 🧪 Testing

### Run All Tests

```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_auth.py

# Run specific test
poetry run pytest tests/test_auth.py::test_login_success
```

### Test Coverage

```bash
# Run tests with coverage
poetry run pytest --cov=src/suca

# Generate HTML coverage report
poetry run pytest --cov=src/suca --cov-report=html

# View report
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
│   ├── session          # Database session
│   ├── client          # Test client (unauthenticated)
│   ├── auth_headers    # JWT token headers
│   └── auth_client     # Authenticated test client
├── test_auth.py        # Authentication tests
├── test_flashcard.py   # Flashcard CRUD tests
├── test_health.py      # Health check tests
└── test_search.py      # Search functionality tests
```

### Using Test Fixtures

```python
def test_create_deck(auth_client: TestClient):
    """Test creating a deck with authentication."""
    response = auth_client.post(
        "/api/v1/flashcard/decks",
        json={"name": "Test Deck"}
    )
    assert response.status_code == 201
```

---

## 🗄️ Database Operations

### Migrations

```bash
# Create new migration (auto-generate from models)
poetry run alembic revision --autogenerate -m "add user table"

# Create empty migration
poetry run alembic revision -m "custom changes"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# Rollback all migrations
poetry run alembic downgrade base

# View migration history
poetry run alembic history

# Check current migration
poetry run alembic current
```

### Using Make Commands

```bash
# Create migration
make migrate

# Apply migrations
make db-upgrade

# Rollback
make db-downgrade

# Reset database (WARNING: destroys data!)
make db-reset

# View history
make db-history
```

### Database Schema

**Main Tables:**
- `flashcard_decks` - User flashcard decks
- `flashcards` - Individual flashcards
- `entry` - Dictionary entries
- `kanji` - Kanji forms
- `reading` - Reading forms
- `sense` - Word meanings
- `gloss` - Definitions
- `example` - Usage examples

---

## 💻 Development

### Using Makefile

```bash
# Show all commands
make help

# Install dependencies
make dev-install

# Run development server
make run

# Run tests
make test
make test-cov

# Code quality
make lint          # Check code
make lint-fix      # Fix issues
make format        # Format code
make type-check    # Type checking

# All checks
make all-checks    # Lint + type-check + test
make ci-checks     # CI pipeline checks

# Database
make migrate       # Create migration
make db-upgrade    # Apply migrations
make db-downgrade  # Rollback
make db-reset      # Reset database

# Cleanup
make clean         # Remove cache files
```

### Code Quality Tools

**Linting & Formatting:**
```bash
# Check code style
poetry run ruff check src/ tests/

# Auto-fix issues
poetry run ruff check --fix src/ tests/

# Format code
poetry run ruff format src/ tests/
```

**Type Checking:**
```bash
poetry run mypy src/
```

**Pre-commit Checks:**
```bash
# Before committing
make ci-checks
```

### Project Dependencies

```bash
# Show dependency tree
poetry show --tree

# Update dependencies
poetry update

# Add new dependency
poetry add package-name

# Add dev dependency
poetry add --group dev package-name

# Check for security issues
poetry run pip-audit
```

---

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG=false` in environment
- [ ] Generate secure `JWT_SECRET_KEY` (32+ chars)
- [ ] Configure PostgreSQL with strong credentials
- [ ] Set up SSL/TLS for database connection
- [ ] Configure CORS for your frontend domain
- [ ] Set up rate limiting (nginx/API Gateway)
- [ ] Enable logging to file/service
- [ ] Set up monitoring (Sentry, DataDog, etc.)
- [ ] Run database migrations
- [ ] Test all endpoints in staging

### Environment Setup

```bash
# Production .env
DEBUG=false
DB_HOST=your-db-host.com
DB_PORT=5432
DB_USER=suca_prod
DB_PASS=secure-password
DB_NAME=suca_production
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
API_TITLE=SUCA API
API_VERSION=1.0.0
```

### Running with Gunicorn

```bash
# Install gunicorn
poetry add gunicorn

# Run with multiple workers
poetry run gunicorn src.suca.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Docker Deployment (Optional)

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --only=main

# Copy application
COPY . .

# Run migrations and start server
CMD poetry run alembic upgrade head && \
    poetry run uvicorn src.suca.main:app --host 0.0.0.0 --port 8000
```

---

## 🏗️ Architecture

### Layered Architecture

```
┌─────────────────────────────────────────┐
│          API Layer (FastAPI)            │
│  - Endpoints (auth, flashcard, search)  │
│  - Request/Response handling            │
│  - JWT authentication                   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Service Layer (Business)        │
│  - FlashcardService                     │
│  - SearchService                        │
│  - Business logic & validation          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│        Database Layer (SQLModel)        │
│  - Models (Flashcard, Deck, Entry)      │
│  - Database operations                  │
│  - Migrations (Alembic)                 │
└─────────────────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns**
   - API layer handles HTTP
   - Service layer contains business logic
   - Database layer manages data

2. **Dependency Injection**
   - FastAPI's DI system for clean dependencies
   - Easy to test and swap implementations

3. **Type Safety**
   - Pydantic for request/response validation
   - SQLModel for database models
   - Full type hints throughout

4. **Error Handling**
   - Custom exceptions (ValidationException, DatabaseException)
   - Structured error responses
   - Proper HTTP status codes

5. **Security First**
   - JWT authentication
   - Password hashing (Bcrypt/Argon2)
   - Rate limiting
   - User data isolation

6. **Testability**
   - Comprehensive test suite
   - Fixtures for auth, database
   - Isolated test database

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/yourusername/SUCA-api.git
   cd SUCA-api
   ```
3. **Create a branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
4. **Install dependencies**
   ```bash
   poetry install
   ```

### Development Workflow

1. **Make your changes**
   - Follow existing code style
   - Add tests for new features
   - Update documentation

2. **Run checks**
   ```bash
   make ci-checks
   ```

3. **Commit your changes**
   ```bash
   git commit -m "feat: add amazing feature"
   ```

4. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

5. **Create Pull Request**
   - Clear description of changes
   - Link related issues
   - Ensure CI passes

### Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding tests
- `refactor:` Code refactoring
- `style:` Code style changes
- `chore:` Maintenance tasks

**Examples:**
```bash
git commit -m "feat: add user profile endpoint"
git commit -m "fix: resolve token expiration bug"
git commit -m "docs: update API endpoint examples"
```

### Code Style

- Use `ruff` for linting and formatting
- Follow PEP 8 guidelines
- Add type hints to all functions
- Write docstrings for public APIs
- Keep functions small and focused

### Testing Requirements

- All new features must have tests
- Maintain >80% code coverage
- Tests should be isolated and deterministic
- Use fixtures for common setups

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **SUCA Team** - [GitHub](https://github.com/yourusername)

---

## 🙏 Acknowledgments

- JMdict project for Japanese dictionary data
- FastAPI for the amazing web framework
- SQLModel for elegant database models
- Poetry for dependency management

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/SUCA-api/issues)
- **Email**: support@suca-api.com
- **Docs**: http://localhost:8000/docs

---

**Built with ❤️ by SUCA Team**
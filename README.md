# SUCA API

A modern Japanese dictionary API built with FastAPI, providing intelligent search capabilities for Japanese-English dictionary entries.

## 🚀 Features

- **Intelligent Search**: Prioritized search results with exact matches, common words, and partial matches
- **Modern Architecture**: Clean separation of concerns with services, schemas, and proper dependency injection
- **Type Safety**: Full type hints with Pydantic models and SQLModel
- **Health Checks**: Comprehensive health monitoring with database status
- **Error Handling**: Structured error responses with proper HTTP status codes
- **Logging**: Structured logging with configurable levels
- **Testing**: Comprehensive test suite with fixtures and mocks

## 📁 Project Structure

```
src/suca/
├── api/                    # API layer
│   ├── deps.py            # Dependency injection
│   └── v1/                # API version 1
│       ├── router.py      # Main API router
│       └── endpoints/     # API endpoints
├── core/                  # Core configuration
│   ├── config.py         # Application settings
│   └── exceptions.py     # Custom exceptions
├── db/                   # Database layer
│   ├── base.py          # Base model classes
│   ├── db.py            # Database configuration
│   └── model.py         # Database models
├── schemas/             # Pydantic schemas
│   ├── base.py         # Base response models
│   ├── search.py       # Search-related schemas
│   └── health.py       # Health check schemas
├── services/           # Business logic layer
│   ├── base.py        # Base service class
│   └── search_service.py # Search business logic
├── utils/             # Utility functions
│   ├── logging.py    # Logging utilities
│   └── text.py       # Text processing utilities
└── main.py           # FastAPI application
```

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SUCA-api
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize the database**
   ```bash
   alembic upgrade head
   ```

## 🚦 Running the Application

### Development
```bash
poetry run uvicorn src.suca.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
poetry run uvicorn src.suca.main:app --host 0.0.0.0 --port 8000
```

## 🔧 Configuration

The application can be configured via environment variables:

- `DATABASE_URL`: Database connection string
- `API_TITLE`: API title (default: "SUCA API")
- `API_VERSION`: API version (default: "1.0.0")
- `DEBUG`: Enable debug mode (default: false)
- `ALLOWED_ORIGINS`: CORS allowed origins (comma-separated)

## 📡 API Endpoints

### Health Check
- `GET /api/v1/health` - Application health status

### Search
- `GET /api/v1/search` - Search dictionary entries
  - Query parameters:
    - `q` (required): Search query
    - `limit` (optional): Maximum results (default: 10, max: 100)
    - `include_rare` (optional): Include rare words (default: false)

## 🧪 Testing

Run the test suite:
```bash
poetry run pytest
```

Run with coverage:
```bash
poetry run pytest --cov=src/suca
```

## 🏗️ Architecture

### Layered Architecture
- **API Layer**: FastAPI endpoints with request/response handling
- **Service Layer**: Business logic and data processing
- **Database Layer**: Data models and database operations
- **Schema Layer**: Request/response models with validation

### Key Design Principles
- **Dependency Injection**: Clean dependency management with FastAPI's DI system
- **Single Responsibility**: Each class/module has a focused purpose
- **Type Safety**: Comprehensive type hints throughout the codebase
- **Error Handling**: Structured exception handling with custom exceptions
- **Configuration Management**: Centralized configuration with environment variables

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
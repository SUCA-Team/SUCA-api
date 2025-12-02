# SUCA API Dockerfile
# This file defines how to build a Docker image for the SUCA API application

# Use Python 3.13 as the base image
FROM python:3.13-slim

# Set working directory inside the container
WORKDIR /app

# Set environment variables
# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1
# Use poetry's virtualenv inside the project
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# Install system dependencies
# Using a more reliable approach with retries
RUN apt-get update -y || true && \
    apt-get install -y --no-install-recommends --fix-missing \
    curl \
    wget \
    ca-certificates \
    postgresql-client \
    gcc \
    g++ \
    make \
    libpq-dev \
    || (apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    ca-certificates \
    gcc \
    g++ \
    make \
    libpq-dev) && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry (Python dependency management tool)
RUN pip install --no-cache-dir poetry==1.7.1

# Copy only dependency files first (for better caching)
COPY pyproject.toml poetry.lock ./

# Install project dependencies
# --no-root: don't install the project itself yet
# --no-dev: don't install development dependencies (use --with dev for dev dependencies)
RUN poetry install --no-root --no-interaction --no-ansi

# Copy the rest of the application code
COPY . .

# Install the project itself
RUN poetry install --no-interaction --no-ansi

# Expose port 8000 (the port our FastAPI app runs on)
EXPOSE 8000

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check to ensure the container is running properly
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Command to run the application
# Use uvicorn to run the FastAPI app
CMD ["poetry", "run", "uvicorn", "src.suca.main:app", "--host", "0.0.0.0", "--port", "8000"]
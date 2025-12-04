# 🐳 Docker Quick Start Guide

## Prerequisites

- Docker Desktop installed ([download here](https://www.docker.com/products/docker-desktop))
- Docker Compose (included with Docker Desktop)

## Quick Start (Development)

```bash
# 1. Copy the Docker environment template
cp .env.docker .env

# 2. Generate and set JWT secret key (optional but recommended)
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env

# 3. Start all services
make docker-up-build

# 4. Run database migrations
make docker-migrate

# 5. Restore dictionary data (required!)
make docker-db-restore FILE=dump.sql

# 5. Access the application
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Health: http://localhost:8000/api/v1/health
```

## Services

### Development Stack (docker-compose.yml)
- **API**: FastAPI application with hot-reload on port 8000
- **Database**: PostgreSQL 16 on port 5432
- **pgAdmin**: Database management UI on port 5050 (optional)

### Production Stack (docker-compose.prod.yml)
- **API**: Optimized production build on port 8000
- **Database**: PostgreSQL 16 with persistent data

## Common Commands

### Starting & Stopping

```bash
# Start all services
make docker-up

# Start with rebuild
make docker-up-build

# Stop all services
make docker-down

# Stop and remove data (fresh start)
make docker-down-volumes

# Restart services
make docker-restart
```

### Viewing Logs

```bash
# All logs
make docker-logs

# API logs only
make docker-logs-api

# Database logs only
make docker-logs-db
```

### Database Operations

```bash
# Run migrations
make docker-migrate

# Create new migration
make docker-migrate-create MSG="add new table"

# Database shell
make docker-db-shell

# Backup database
make docker-db-backup

# Restore database
make docker-db-restore FILE=backup.sql

# Reset database (WARNING: deletes all data)
make docker-db-reset
```

### Development

```bash
# Run tests in Docker
make docker-test

# Run tests with coverage
make docker-test-cov

# Lint code
make docker-lint

# Format code
make docker-format

# Shell into API container
make docker-shell

# Python shell in container
make docker-python
```

### Production Deployment

```bash
# Build production image
docker build -t suca-api:prod .

# Start production stack
make docker-prod-build

# View production logs
make docker-prod-logs

# Stop production
make docker-prod-down
```

## Environment Variables

Create a `.env` file with these variables:

```env
# Database
DB_USER=postgres
DB_PASS=your_secure_password
DB_NAME=suca

# JWT Secret (REQUIRED!)
JWT_SECRET_KEY=your-secret-key-here

# Debug (optional)
DEBUG=true
SQLALCHEMY_ECHO=false
```

## pgAdmin (Database UI)

To start pgAdmin:

```bash
# Start pgAdmin
make docker-tools-up

# Access at http://localhost:5050
# Email: admin@suca.local
# Password: admin

# Connect to database:
# Host: db
# Port: 5432
# Username: postgres
# Password: (from your .env)
# Database: suca
```

## Development Workflow

```bash
# 1. Make changes to code in src/
# Code changes are automatically detected (hot-reload)

# 2. If you change dependencies:
make docker-up-build

# 3. If you change database models:
make docker-migrate-create MSG="describe changes"
make docker-migrate

# 4. Test your changes:
make docker-test
```

## Troubleshooting

**Port already in use:**
```bash
# Stop local services first
make docker-down
# Or change ports in docker-compose.yml
```

**Database connection failed:**
```bash
# Check database is running
make docker-ps

# View database logs
make docker-logs-db

# Restart database
docker-compose restart db
```

**Permission denied errors:**
```bash
# On Linux, you may need to fix permissions
sudo chown -R $USER:$USER .
```

**Clean slate (removes all data!):**
```bash
make docker-fresh
```

## File Structure

```
.
├── Dockerfile              # Production image
├── Dockerfile.dev          # Development image (hot-reload)
├── docker-compose.yml      # Development stack
├── docker-compose.prod.yml # Production stack
├── .dockerignore          # Files to exclude from image
└── .env.docker            # Environment template
```

## Tips

1. **Hot Reload**: Code changes in `src/` are automatically detected in development mode
2. **Data Persistence**: Database data is stored in Docker volumes
3. **Clean Rebuild**: Use `make docker-rebuild` for a clean build
4. **Resource Usage**: Check with `make docker-stats`
5. **Logs**: Always check logs when debugging: `make docker-logs`

## Quick Reference

| Command | Description |
|---------|-------------|
| `make docker-up` | Start services |
| `make docker-down` | Stop services |
| `make docker-logs` | View logs |
| `make docker-shell` | Shell into container |
| `make docker-migrate` | Run migrations |
| `make docker-test` | Run tests |
| `make docker-clean` | Clean up |

## Next Steps

- Read the main [README.md](README.md) for API documentation
- Check [WORKFLOW.md](WORKFLOW.md) for development workflow
- View API docs at http://localhost:8000/docs

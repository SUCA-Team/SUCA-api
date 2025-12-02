# Development Workflow Guide

## 🔐 JWT Secret Key Management

The application requires a `JWT_SECRET_KEY` for authentication. Here's how it's handled in each environment:

### 1. **Local Development**

**Setup (First Time)**
```bash
# Generate a secure secret key
openssl rand -hex 32

# Add it to your .env file
echo "JWT_SECRET_KEY=<generated-key>" >> .env
```

**Your `.env` file should contain:**
```env
ENV=dev
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=your_user
DB_PASS=your_password
DB_NAME=jmdict
DEBUG=true
JWT_SECRET_KEY=<your-generated-key>
```

**Run the server:**
```bash
poetry run uvicorn src.suca.main:app --reload
```

---

### 2. **Docker Development**

**Setup:**
```bash
# Generate a secret key
openssl rand -hex 32

# Edit .env.docker and replace CHANGE_ME_IN_PRODUCTION_USE_OPENSSL_RAND_HEX_32
# with your generated key
```

**Run with Docker Compose:**
```bash
# Copy .env.docker to .env if using docker-compose
cp .env.docker .env

# Or set it inline
JWT_SECRET_KEY=$(openssl rand -hex 32) docker-compose up
```

**Alternative: Use a separate `.env` file:**
```bash
# Create .env with your secrets
cat > .env << EOF
JWT_SECRET_KEY=$(openssl rand -hex 32)
DB_USER=cynmeiciel
DB_PASS=your_password
DB_NAME=jmdict
ENV=dev
DEBUG=true
EOF

# Start services
docker-compose up
```

---

### 3. **GitHub Actions CI**

**Already configured!** ✓

The CI workflow (`.github/workflows/ci.yml`) sets `JWT_SECRET_KEY` as an environment variable:
```yaml
env:
  JWT_SECRET_KEY: test-secret-key-for-ci-only
  DEBUG: true
```

Tests will automatically use this test key. No secrets needed in GitHub for basic CI.

---

### 4. **Production Deployment**

**⚠️ CRITICAL: Never commit production secrets to git!**

#### Option A: Environment Variables (Recommended)
```bash
# On your production server
export JWT_SECRET_KEY=$(openssl rand -hex 32)
export DEBUG=false

# Run the app
uvicorn src.suca.main:app --host 0.0.0.0 --port 8000
```

#### Option B: GitHub Secrets (for GitHub Actions deployment)
1. Go to your repo → Settings → Secrets and variables → Actions
2. Add new repository secret:
   - Name: `JWT_SECRET_KEY`
   - Value: (generate with `openssl rand -hex 32`)

3. Update your deployment workflow:
```yaml
env:
  JWT_SECRET_KEY: ${{ secrets.JWT_SECRET_KEY }}
  DEBUG: false
```

#### Option C: Cloud Platform Secrets
- **AWS**: Use AWS Secrets Manager
- **Azure**: Use Azure Key Vault
- **Google Cloud**: Use Secret Manager
- **Heroku**: `heroku config:set JWT_SECRET_KEY=xxx`
- **Railway/Render**: Set in environment variables dashboard

---

## 📋 Complete Workflow

### New Developer Setup
```bash
# 1. Clone the repo
git clone <repo-url>
cd SUCA-api

# 2. Install dependencies
poetry install --with dev

# 3. Create .env file
cp .env.template .env

# 4. Generate JWT secret
openssl rand -hex 32
# Copy the output and add to .env as JWT_SECRET_KEY=<output>

# 5. Configure database settings in .env
# Edit DB_USER, DB_PASS, DB_NAME

# 6. Run migrations
poetry run alembic upgrade head

# 7. Start the server
poetry run uvicorn src.suca.main:app --reload
```

### Docker Workflow
```bash
# 1. Set your secrets
cp .env.docker .env
# Edit .env and set JWT_SECRET_KEY

# 2. Build and run
docker-compose up --build

# 3. Run migrations (in another terminal)
docker-compose exec api poetry run alembic upgrade head
```

### CI/CD Workflow
```bash
# 1. Push to GitHub
git push origin main

# 2. GitHub Actions automatically:
#    - Runs linting (Ruff)
#    - Runs type checking (mypy)
#    - Runs tests with coverage
#    - Reports results
```

---

## 🔒 Security Best Practices

1. **Never commit `.env` files** - Already in `.gitignore` ✓
2. **Use different secrets for each environment** - Dev, staging, production should all have unique keys
3. **Rotate secrets periodically** - Generate new keys every 90 days
4. **Use strong secrets** - Always use `openssl rand -hex 32` (64 characters)
5. **Limit secret access** - Only give production secrets to necessary team members

---

## 🚨 Troubleshooting

**Error: "JWT_SECRET_KEY must be set in production!"**
- Solution: Add `JWT_SECRET_KEY` to your `.env` file or environment variables

**Error: "No module named 'src'"**
- Solution: Run commands with `poetry run` prefix

**Error: Database connection failed**
- Solution: Check your database is running and credentials in `.env` are correct

**Docker: "address already in use"**
- Solution: Stop local server first or change port in `docker-compose.yml`

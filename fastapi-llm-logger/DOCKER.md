# Docker Deployment Guide

This guide covers all Docker-related operations for the LLM Platform backend.

## Table of Contents

1. [Docker Files Overview](#docker-files-overview)
2. [Quick Start](#quick-start)
3. [Development Setup](#development-setup)
4. [Production Deployment](#production-deployment)
5. [Docker Compose](#docker-compose)
6. [Common Commands](#common-commands)
7. [Troubleshooting](#troubleshooting)

---

## Docker Files Overview

### Files Included

| File | Purpose |
|------|---------|
| `Dockerfile` | Standard production-ready image |
| `Dockerfile.dev` | Development image with hot reload |
| `Dockerfile.prod` | Optimized multi-stage production build |
| `docker-compose.yml` | Production compose configuration |
| `docker-compose.dev.yml` | Development with local MongoDB |
| `.dockerignore` | Files to exclude from image |

---

## Quick Start

### Using Docker (Standalone)

**1. Build the image:**
```bash
docker build -t llm-backend .
```

**2. Run the container:**
```bash
docker run -d \
  --name llm-backend \
  -p 8000:8000 \
  -e MONGODB_URI="your_mongodb_uri" \
  -e OPENAI_API_KEY="your_api_key" \
  llm-backend
```

**3. Check logs:**
```bash
docker logs -f llm-backend
```

**4. Test the API:**
```bash
curl http://localhost:8000/status
```

---

## Development Setup

### Option 1: Docker Compose with Local MongoDB

This setup includes:
- Backend API with hot reload
- Local MongoDB instance
- Mongo Express (web UI for MongoDB)

**1. Start all services:**
```bash
docker-compose -f docker-compose.dev.yml up -d
```

**2. Access services:**
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Mongo Express: http://localhost:8081 (admin/admin)

**3. View logs:**
```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Backend only
docker-compose -f docker-compose.dev.yml logs -f backend

# MongoDB only
docker-compose -f docker-compose.dev.yml logs -f mongodb
```

**4. Stop services:**
```bash
docker-compose -f docker-compose.dev.yml down
```

**5. Stop and remove volumes (clean slate):**
```bash
docker-compose -f docker-compose.dev.yml down -v
```

### Option 2: Development Docker with Cloud MongoDB

**1. Build dev image:**
```bash
docker build -f Dockerfile.dev -t llm-backend-dev .
```

**2. Run with .env file:**
```bash
docker run -d \
  --name llm-backend-dev \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd):/app \
  llm-backend-dev
```

The `-v $(pwd):/app` mounts your local code for hot reload.

### Local MongoDB Connection String

When using local MongoDB from docker-compose:

```bash
MONGODB_URI=mongodb://admin:password@mongodb:27017/llm_experiment?authSource=admin
```

**Note:** Use `mongodb` as hostname (not `localhost`) when connecting from Docker.

---

## Production Deployment

### Option 1: Optimized Multi-Stage Build

**1. Build production image:**
```bash
docker build -f Dockerfile.prod -t llm-backend-prod .
```

**2. Run in production mode:**
```bash
docker run -d \
  --name llm-backend-prod \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  llm-backend-prod
```

This runs with 4 Uvicorn workers for better performance.

### Option 2: Docker Compose (Production)

**1. Ensure `.env` file exists:**
```bash
cp .env.example .env
# Edit .env with production values
```

**2. Start production services:**
```bash
docker-compose up -d
```

**3. Scale workers:**
```bash
docker-compose up -d --scale backend=3
```

**4. Monitor:**
```bash
docker-compose ps
docker-compose logs -f backend
```

### Option 3: Deploy to Cloud (Render, AWS, GCP)

#### Render.com

Render automatically detects and uses your `Dockerfile`.

**render.yaml (optional):**
```yaml
services:
  - type: web
    name: llm-backend
    env: docker
    dockerfilePath: ./Dockerfile
    envVars:
      - key: MONGODB_URI
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: LITELLM_MODEL
        value: gpt-4o-mini
      - key: MONGO_DB
        value: llm_experiment
```

#### AWS ECS/Fargate

**1. Build and tag:**
```bash
docker build -f Dockerfile.prod -t llm-backend:latest .
```

**2. Push to ECR:**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag llm-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/llm-backend:latest

docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/llm-backend:latest
```

#### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT-ID/llm-backend

# Deploy
gcloud run deploy llm-backend \
  --image gcr.io/PROJECT-ID/llm-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars MONGODB_URI="...",OPENAI_API_KEY="..."
```

---

## Docker Compose

### Production Compose

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart specific service
docker-compose restart backend

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Development Compose

```bash
# Start with local MongoDB
docker-compose -f docker-compose.dev.yml up -d

# Rebuild after code changes
docker-compose -f docker-compose.dev.yml up -d --build

# Execute commands in container
docker-compose -f docker-compose.dev.yml exec backend python -c "print('Hello')"

# Access backend shell
docker-compose -f docker-compose.dev.yml exec backend bash
```

---

## Common Commands

### Building

```bash
# Standard build
docker build -t llm-backend .

# Development build
docker build -f Dockerfile.dev -t llm-backend-dev .

# Production build
docker build -f Dockerfile.prod -t llm-backend-prod .

# Build with no cache
docker build --no-cache -t llm-backend .

# Build with build args
docker build --build-arg VERSION=1.0.0 -t llm-backend:1.0.0 .
```

### Running

```bash
# Run in foreground
docker run -p 8000:8000 --env-file .env llm-backend

# Run in background (detached)
docker run -d -p 8000:8000 --env-file .env llm-backend

# Run with custom name
docker run -d --name my-backend -p 8000:8000 --env-file .env llm-backend

# Run with volume mount (dev)
docker run -d -p 8000:8000 -v $(pwd):/app --env-file .env llm-backend-dev

# Run with environment variables inline
docker run -d -p 8000:8000 \
  -e MONGODB_URI="..." \
  -e OPENAI_API_KEY="..." \
  llm-backend
```

### Managing Containers

```bash
# List running containers
docker ps

# List all containers
docker ps -a

# Stop container
docker stop llm-backend

# Start stopped container
docker start llm-backend

# Restart container
docker restart llm-backend

# Remove container
docker rm llm-backend

# Force remove running container
docker rm -f llm-backend

# View logs
docker logs llm-backend

# Follow logs
docker logs -f llm-backend

# Last 100 lines
docker logs --tail 100 llm-backend
```

### Inspecting

```bash
# Container details
docker inspect llm-backend

# Container stats (CPU, memory)
docker stats llm-backend

# Execute command in running container
docker exec llm-backend python --version

# Interactive shell
docker exec -it llm-backend bash

# Check health status
docker inspect --format='{{.State.Health.Status}}' llm-backend
```

### Cleaning Up

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove all unused data
docker system prune

# Remove everything (careful!)
docker system prune -a --volumes

# Remove specific image
docker rmi llm-backend
```

---

## Environment Variables

### Required Variables

```bash
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/llm_experiment
OPENAI_API_KEY=sk-proj-xxxxx
```

### Optional Variables

```bash
MONGO_DB=llm_experiment
LITELLM_MODEL=gpt-4o-mini
```

### Setting Variables

**Method 1: .env file**
```bash
docker run --env-file .env llm-backend
```

**Method 2: Inline**
```bash
docker run -e MONGODB_URI="..." -e OPENAI_API_KEY="..." llm-backend
```

**Method 3: Docker Compose**
```yaml
services:
  backend:
    environment:
      - MONGODB_URI=${MONGODB_URI}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

---

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker logs llm-backend
```

**Common issues:**
- Missing environment variables
- MongoDB connection failed
- Port 8000 already in use

**Solutions:**
```bash
# Check if port is in use
lsof -i :8000

# Use different port
docker run -p 8001:8000 llm-backend

# Verify env vars
docker exec llm-backend env | grep MONGODB
```

### MongoDB Connection Issues

**From Docker to localhost MongoDB:**
```bash
# Don't use localhost, use host.docker.internal
MONGODB_URI=mongodb://host.docker.internal:27017/llm_experiment
```

**From Docker to Docker MongoDB:**
```bash
# Use container name or service name
MONGODB_URI=mongodb://mongodb:27017/llm_experiment
```

### Health Check Failing

**Check health status:**
```bash
docker inspect --format='{{json .State.Health}}' llm-backend | jq
```

**Manual health check:**
```bash
docker exec llm-backend curl http://localhost:8000/status
```

### Out of Memory

**Check memory usage:**
```bash
docker stats llm-backend
```

**Increase memory limit:**
```bash
docker run --memory="2g" llm-backend
```

### Slow Build Times

**Use BuildKit:**
```bash
DOCKER_BUILDKIT=1 docker build -t llm-backend .
```

**Use cache from registry:**
```bash
docker build --cache-from llm-backend:latest -t llm-backend:new .
```

### Container Stops Unexpectedly

**Check exit code:**
```bash
docker ps -a
```

**View last logs:**
```bash
docker logs --tail 50 llm-backend
```

**Common exit codes:**
- 0: Normal exit
- 1: Application error
- 137: Out of memory (OOM)
- 139: Segmentation fault

---

## Performance Tuning

### Production Settings

**1. Use multiple workers:**
```bash
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**2. Limit resources:**
```bash
docker run --memory="2g" --cpus="2" llm-backend
```

**3. Use production-optimized image:**
```bash
docker build -f Dockerfile.prod -t llm-backend-prod .
```

### Monitoring

**Real-time stats:**
```bash
docker stats llm-backend
```

**Export metrics:**
```bash
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

---

## Security Best Practices

✅ **Non-root user** - Images run as `appuser`, not root
✅ **No secrets in image** - Use environment variables
✅ **Minimal base image** - Using `python:3.11-slim`
✅ **Health checks** - Built-in health monitoring
✅ **Read-only filesystem** - Consider adding `--read-only` flag
✅ **.dockerignore** - Excludes sensitive files

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -f Dockerfile.prod -t llm-backend:${{ github.sha }} .

      - name: Push to registry
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker push llm-backend:${{ github.sha }}
```

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)

---

**Ready to deploy!** 🚀

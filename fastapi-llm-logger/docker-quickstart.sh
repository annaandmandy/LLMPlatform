#!/bin/bash

# Docker Quick Start Script for LLM Backend
# This script provides quick commands to build and run the backend

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== LLM Backend Docker Quick Start ===${NC}\n"

# Function to print usage
usage() {
    echo "Usage: ./docker-quickstart.sh [command]"
    echo ""
    echo "Commands:"
    echo "  build          Build the Docker image"
    echo "  build-dev      Build development image"
    echo "  build-prod     Build production image"
    echo "  run            Run the container"
    echo "  run-dev        Run development container with hot reload"
    echo "  stop           Stop the container"
    echo "  logs           View container logs"
    echo "  shell          Open shell in running container"
    echo "  clean          Remove containers and images"
    echo "  compose-up     Start with docker-compose (production)"
    echo "  compose-dev    Start with docker-compose (development with MongoDB)"
    echo "  compose-down   Stop docker-compose services"
    echo "  test           Test the API endpoint"
    echo "  help           Show this help message"
    echo ""
}

# Check if .env file exists
check_env() {
    if [ ! -f .env ]; then
        echo -e "${RED}Error: .env file not found!${NC}"
        echo "Please create .env file from .env.example:"
        echo "  cp .env.example .env"
        echo "  # Edit .env with your configuration"
        exit 1
    fi
}

# Build standard image
build() {
    echo -e "${GREEN}Building standard Docker image...${NC}"
    docker build -t llm-backend:latest .
    echo -e "${GREEN}✓ Build complete!${NC}"
}

# Build development image
build_dev() {
    echo -e "${GREEN}Building development Docker image...${NC}"
    docker build -f Dockerfile.dev -t llm-backend:dev .
    echo -e "${GREEN}✓ Development build complete!${NC}"
}

# Build production image
build_prod() {
    echo -e "${GREEN}Building production Docker image...${NC}"
    docker build -f Dockerfile.prod -t llm-backend:prod .
    echo -e "${GREEN}✓ Production build complete!${NC}"
}

# Run container
run() {
    check_env
    echo -e "${GREEN}Starting container...${NC}"
    docker run -d \
        --name llm-backend \
        -p 8000:8000 \
        --env-file .env \
        --restart unless-stopped \
        llm-backend:latest
    echo -e "${GREEN}✓ Container started!${NC}"
    echo "API available at: http://localhost:8000"
    echo "API Docs: http://localhost:8000/docs"
}

# Run development container
run_dev() {
    check_env
    echo -e "${GREEN}Starting development container with hot reload...${NC}"
    docker run -d \
        --name llm-backend-dev \
        -p 8000:8000 \
        --env-file .env \
        -v "$(pwd):/app" \
        llm-backend:dev
    echo -e "${GREEN}✓ Development container started!${NC}"
    echo "API available at: http://localhost:8000"
    echo "Code changes will auto-reload!"
}

# Stop container
stop() {
    echo -e "${GREEN}Stopping container...${NC}"
    docker stop llm-backend 2>/dev/null || docker stop llm-backend-dev 2>/dev/null || true
    docker rm llm-backend 2>/dev/null || docker rm llm-backend-dev 2>/dev/null || true
    echo -e "${GREEN}✓ Container stopped!${NC}"
}

# View logs
logs() {
    echo -e "${GREEN}Viewing logs (Ctrl+C to exit)...${NC}"
    docker logs -f llm-backend 2>/dev/null || docker logs -f llm-backend-dev 2>/dev/null
}

# Open shell
shell() {
    echo -e "${GREEN}Opening shell in container...${NC}"
    docker exec -it llm-backend bash 2>/dev/null || docker exec -it llm-backend-dev bash 2>/dev/null
}

# Clean up
clean() {
    echo -e "${GREEN}Cleaning up containers and images...${NC}"
    docker stop llm-backend 2>/dev/null || true
    docker stop llm-backend-dev 2>/dev/null || true
    docker rm llm-backend 2>/dev/null || true
    docker rm llm-backend-dev 2>/dev/null || true
    docker rmi llm-backend:latest 2>/dev/null || true
    docker rmi llm-backend:dev 2>/dev/null || true
    docker rmi llm-backend:prod 2>/dev/null || true
    echo -e "${GREEN}✓ Cleanup complete!${NC}"
}

# Docker Compose up (production)
compose_up() {
    check_env
    echo -e "${GREEN}Starting services with docker-compose...${NC}"
    docker-compose up -d
    echo -e "${GREEN}✓ Services started!${NC}"
    docker-compose ps
}

# Docker Compose up (development)
compose_dev() {
    check_env
    echo -e "${GREEN}Starting development services with docker-compose...${NC}"
    docker-compose -f docker-compose.dev.yml up -d
    echo -e "${GREEN}✓ Development services started!${NC}"
    echo ""
    echo "Services available:"
    echo "  - Backend API: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - MongoDB: localhost:27017"
    echo "  - Mongo Express: http://localhost:8081 (admin/admin)"
    echo ""
    docker-compose -f docker-compose.dev.yml ps
}

# Docker Compose down
compose_down() {
    echo -e "${GREEN}Stopping docker-compose services...${NC}"
    docker-compose down 2>/dev/null || docker-compose -f docker-compose.dev.yml down 2>/dev/null
    echo -e "${GREEN}✓ Services stopped!${NC}"
}

# Test API
test() {
    echo -e "${GREEN}Testing API endpoint...${NC}"
    echo ""
    curl -s http://localhost:8000/status | jq '.' 2>/dev/null || curl -s http://localhost:8000/status
    echo ""
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ API is responding!${NC}"
    else
        echo -e "${RED}✗ API is not responding${NC}"
        exit 1
    fi
}

# Main command handler
case "${1}" in
    build)
        build
        ;;
    build-dev)
        build_dev
        ;;
    build-prod)
        build_prod
        ;;
    run)
        run
        ;;
    run-dev)
        run_dev
        ;;
    stop)
        stop
        ;;
    logs)
        logs
        ;;
    shell)
        shell
        ;;
    clean)
        clean
        ;;
    compose-up)
        compose_up
        ;;
    compose-dev)
        compose_dev
        ;;
    compose-down)
        compose_down
        ;;
    test)
        test
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo -e "${RED}Unknown command: ${1}${NC}\n"
        usage
        exit 1
        ;;
esac

.PHONY: install dev test lint format clean docker-build run setup worker

# Installation commands
install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt
	pip install black isort mypy pytest-cov flake8

# Development commands
run:
	python run.py

worker:
	celery -A worker.celery_app worker --loglevel=info

setup:
	cp .env.example .env
	@echo "✅ Created .env file from template"
	@echo "📝 Please edit .env with your API keys"

# Testing commands
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=app --cov-report=html

# Code quality commands  
lint:
	black --check app/ tests/ worker/
	isort --check-only app/ tests/ worker/
	mypy app/

format:
	black app/ tests/ worker/
	isort app/ tests/ worker/

# Cleanup commands
clean:
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-restart:
	docker-compose restart

# Development helpers
dev-server:
	uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

redis-start:
	redis-server

redis-cli:
	redis-cli

# Help command
help:
	@echo "Available commands:"
	@echo "  setup        - Create .env file from template"
	@echo "  install      - Install production dependencies"
	@echo "  dev          - Install development dependencies"
	@echo "  run          - Start the application"
	@echo "  worker       - Start Celery worker"
	@echo "  dev-server   - Start development server with auto-reload"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  lint         - Check code formatting"
	@echo "  format       - Format code"
	@echo "  clean        - Clean up cache files"
	@echo "  docker-build - Build Docker containers"
	@echo "  docker-up    - Start Docker services"
	@echo "  docker-down  - Stop Docker services"
	@echo "  docker-logs  - View Docker logs"
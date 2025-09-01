.PHONY: help up down build seed test clean logs

help: ## Show this help message
	@echo "Project Portfolio Management System - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start all services
	docker-compose up -d
	@echo "🚀 Services starting... Check status with 'make logs'"

down: ## Stop all services
	docker-compose down
	@echo "🛑 Services stopped"

build: ## Build and start services
	docker-compose up -d --build
	@echo "🔨 Services built and started"

seed: ## Seed database with comprehensive PPM+AI data
	@echo "🌱 Seeding database with comprehensive PPM+AI data..."
	docker-compose exec api python scripts/seed.py

seed-basic: ## Seed database with basic sample data
	@echo "🌱 Seeding database with basic data..."
	docker-compose exec api python scripts/seed_data.py

seed-ai: ## Seed database with AI-First specific data
	@echo "🤖 Seeding database with AI-First data..."
	docker-compose exec api python scripts/seed_ai_first.py

clear-db: ## Clear database (WARNING: removes all data)
	@echo "🗑️  Clearing database..."
	docker-compose exec api python scripts/clear_db.py

test: ## Run tests
	@echo "🧪 Running tests..."
	docker-compose exec api python -m pytest

clean: ## Clean up all data and containers
	docker-compose down -v
	docker system prune -f
	@echo "🧹 Cleanup completed"

# Additional test commands
test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	python -m pytest tests/ -v -m "unit" --tb=short

test-integration: ## Run integration tests only
	@echo "🧪 Running integration tests..."
	python -m pytest tests/ -v -m "integration" --tb=short

test-api: ## Run API tests only
	@echo "🧪 Running API tests..."
	python -m pytest tests/test_api.py -v --tb=short

test-ai: ## Run AI functionality tests only
	@echo "🧪 Running AI tests..."
	python -m pytest tests/ -v -m "ai" --tb=short

test-db: ## Run database tests only
	@echo "🧪 Running database tests..."
	python -m pytest tests/test_database.py -v --tb=short

test-basic: ## Run basic configuration tests
	@echo "🧪 Running basic tests..."
	python -m pytest tests/test_basic.py -v --tb=short

test-coverage: ## Run tests with detailed coverage report
	@echo "🧪 Running tests with coverage..."
	python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml

test-fast: ## Run fast tests only (excluding slow/external)
	@echo "🧪 Running fast tests..."
	python -m pytest tests/ -v -m "not slow and not external" --tb=short

test-smoke: ## Run smoke tests for basic system health
	@echo "🧪 Running smoke tests..."
	python -m pytest tests/ -v -m "smoke" --tb=short

logs: ## Show service logs
	docker-compose logs -f

logs-api: ## Show API service logs
	docker-compose logs -f api

logs-db: ## Show database logs
	docker-compose logs -f db

logs-chroma: ## Show Chroma logs
	docker-compose logs -f chroma

status: ## Show service status
	docker-compose ps

restart: ## Restart all services
	docker-compose restart
	@echo "🔄 Services restarted"

restart-api: ## Restart API service
	docker-compose restart api
	@echo "🔄 API service restarted"

shell: ## Open shell in API container
	docker-compose exec api bash

db-shell: ## Open shell in database
	docker-compose exec db psql -U app -d app

health: ## Check service health
	@echo "🏥 Checking service health..."
	@curl -s http://localhost/health || echo "❌ Services not responding"
	@curl -s http://localhost:8001/health || echo "❌ API not responding"
	@curl -s http://localhost:8000/api/v1/heartbeat || echo "❌ Chroma not responding"

setup: ## Initial setup (first time only)
	@echo "🚀 Initial setup..."
	make build
	@echo "⏳ Waiting for services to be ready..."
	@sleep 30
	make seed
	@echo "✅ Setup completed! Visit http://localhost"

dev: ## Start in development mode
	docker-compose -f docker-compose.yml up -d
	@echo "🔧 Development mode started"
	@echo "📱 Frontend: http://localhost"
	@echo "🔌 API: http://localhost:8001"
	@echo "📚 API Docs: http://localhost:8001/docs"

prod: ## Start in production mode
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "🚀 Production mode started"

backup: ## Backup database
	@echo "💾 Creating database backup..."
	docker-compose exec db pg_dump -U app app > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup completed"

restore: ## Restore database from backup file
	@echo "📥 Restoring database from backup..."
	@read -p "Enter backup filename: " filename; \
	docker-compose exec -T db psql -U app -d app < $$filename
	@echo "✅ Restore completed"

monitor: ## Monitor system resources
	@echo "📊 System monitoring..."
	docker stats --no-stream

update: ## Update all services
	@echo "🔄 Updating services..."
	docker-compose pull
	docker-compose up -d --build
	@echo "✅ Update completed"

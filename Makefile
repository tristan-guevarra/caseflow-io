.PHONY: up down build migrate seed test logs shell-backend shell-db lint reset test-frontend

# spin up everything
up:
	docker compose up -d --build
	@echo "✅ AI CaseFlow is running"
	@echo "   Frontend: http://localhost:3000"
	@echo "   API Docs: http://localhost:8000/docs"

# stop all containers
down:
	docker compose down

# rebuild without cache
build:
	docker compose build --no-cache

# run db migrations
migrate:
	docker compose exec backend alembic upgrade head
	@echo "✅ Migrations applied"

# create a new migration
migration:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

# seed demo data
seed:
	docker compose exec backend python -m scripts.seed
	@echo "✅ Demo data seeded"

# run backend tests
test:
	docker compose exec backend python -m pytest tests/ -v --tb=short

# run frontend tests
test-frontend:
	docker compose exec frontend npm test

# tail all logs
logs:
	docker compose logs -f

# tail backend and worker logs
logs-backend:
	docker compose logs -f backend worker

# get a shell in the backend container
shell-backend:
	docker compose exec backend bash

# open psql in the db container
shell-db:
	docker compose exec postgres psql -U caseflow -d caseflow

# run linters
lint:
	docker compose exec backend python -m ruff check app/
	docker compose exec frontend npm run lint

# nuke everything and start fresh
reset:
	docker compose down -v
	docker compose up -d --build
	@sleep 5
	$(MAKE) migrate
	$(MAKE) seed
	@echo "✅ Full reset complete"

# check container status
status:
	docker compose ps

verify:
	ruff check .
	ruff format --check .
	pytest -q
	python -m evals.run --mode replay
	docker build -t reliability-agent-platform:latest .


.PHONY: install dev test lint fmt up down logs rules

install:
	python -m venv .venv
	.venv/bin/pip install -e ".[dev]"

dev:
	uvicorn api.main:app --reload --port 8000

test:
	pytest -q

lint:
	ruff check .
	ruff format --check .

fmt:
	ruff check --fix .
	ruff format .

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f api

# Copy AGENTS.md to the files other AI tools read.
rules:
	sh scripts/sync_rules.sh

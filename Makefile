.PHONY: install develop install-dev test lint docs docs-serve run clean docker-build docker-up admin-user prune-stats
install:
	python -m pip install -e .
develop install-dev:
	python -m pip install -e '.[dev]'
test:
	python -m pytest
lint:
	python -m ruff check app tests
docs:
	python -m mkdocs build
docs-serve:
	python -m mkdocs serve
run:
	python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
admin-user:
	python -m app.admin bootstrap
prune-stats:
	python -m app.admin prune-stats --older-than 90d
clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov build dist *.egg-info site
	find app -type d -name __pycache__ -prune -exec rm -rf {} +
docker-build:
	docker build -t voice-box .
docker-up:
	docker compose up --build

install:
	. .venv/bin/activate && pip install -e .

develop:
	. .venv/bin/activate && pip install -r requirements-dev.txt

test:
	PYTHONPATH=. .venv/bin/pytest
lint:
	.venv/bin/ruff check .
docs:
	mkdocs build
run:
	.venv/bin/uvicorn app.main:app --reload
clean:
	rm -rf .venv output/* tmp/* data/* site/
docker-build:
	docker build -t voicebox .
docker-up:
	docker compose up --build

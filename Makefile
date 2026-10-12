.PHONY: setup lint test data train api web guard

guard:
	uv run python scripts/guard.py

setup:
	uv venv .venv
	uv pip install -r backend/requirements.txt -e ml
	cd frontend && npm install

lint:
	uv run ruff check .
	uv run black --check .
	cd frontend && npm run lint

test:
	uv run pytest -q ml/tests backend/tests
	cd frontend && npm run test

data:
	uv run python -m epk.data --out data --seed 42

train:
	uv run python -m epk.train --config ml/configs/train.yaml

api:
	uv run uvicorn app.main:app --reload --app-dir backend

web:
	cd frontend && npm run dev

seed:
	uv run python -m epk.seed_data

docker-up:
	docker-compose up --build

evidence:
	python scripts/collect_evidence.py --phase $(PHASE) --cmd "tests::make test" --cmd "lint::make lint"

review-bundle:
	python scripts/build_review_bundle.py

redflags:
	python scripts/redflags.py

verify-all: lint test redflags evidence

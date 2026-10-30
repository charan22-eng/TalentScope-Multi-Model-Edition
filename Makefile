.PHONY: setup lint test data train api web guard demo-setup demo-smoke

guard:
	uv run python scripts/guard.py

setup:
	uv venv .venv --python 3.11
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
	python ml/src/epk/train_all.py --profile $${PROFILE:-fast}

final:
	python ml/src/epk/final_eval.py --variant $${VARIANT:-nonlinear}

final-variants:
	python ml/src/epk/sensitivity.py

api:
	uv run uvicorn backend.app.main:app --reload --reload-dir backend --reload-dir ml/src --port 8000

web:
	cd frontend && npm run dev

demo-setup:
	uv run python scripts/demo_setup.py

demo-smoke:
	uv run python scripts/demo_smoke.py

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

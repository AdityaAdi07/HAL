up:
	docker-compose up -d postgres

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m app.db.seed

synth:
	cd backend && python -m app.synthetic.generate --scenario A --months 6 --seed 42 && python -m app.db.seed

api:
	cd backend && uvicorn app.main:app --reload --port 8000

web:
	cd frontend && npm run dev

test:
	cd backend && pytest tests
	cd frontend && npm run test

lint:
	cd backend && ruff check . && mypy .
	cd frontend && npm run lint && npx tsc --noEmit

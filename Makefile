.PHONY: up down reset logs test lint format seed

up:
	docker compose up --build -d

down:
	docker compose down

reset:
	docker compose down -v && docker compose up --build -d

logs:
	docker compose logs -f

test:
	docker compose exec backend pytest -q

lint:
	docker compose exec backend ruff check .
	docker compose exec backend ruff format --check .
	docker compose exec frontend npm run lint
	docker compose exec frontend npm run format:check
	docker compose exec frontend npx tsc --noEmit -p .

format:
	docker compose exec backend ruff format .
	docker compose exec frontend npm run format

seed:
	docker compose exec backend python -m app.seed

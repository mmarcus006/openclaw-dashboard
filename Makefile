.PHONY: setup dev backend frontend types test test-backend test-frontend build serve lint

BACKEND_DIR = backend
FRONTEND_DIR = frontend
VENV = $(BACKEND_DIR)/.venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

setup:
	cd $(BACKEND_DIR) && python3 -m venv .venv && $(PIP) install -e ".[dev]"
	cd $(FRONTEND_DIR) && npm install

dev:
	@echo "Starting backend + frontend..."
	@make backend & make frontend & wait

backend:
	cd $(BACKEND_DIR) && $(VENV)/bin/uvicorn app.main:app --host 127.0.0.1 --port 8400 --reload

frontend:
	cd $(FRONTEND_DIR) && npm run dev

types:
	cd $(FRONTEND_DIR) && npx openapi-typescript http://127.0.0.1:8400/openapi.json -o src/types/generated.ts

test: test-backend test-frontend

test-backend:
	cd $(BACKEND_DIR) && $(VENV)/bin/pytest --cov=app --cov-report=term-missing

test-frontend:
	cd $(FRONTEND_DIR) && npm run test

build:
	cd $(FRONTEND_DIR) && npm run build
	rm -rf $(BACKEND_DIR)/static
	cp -r $(FRONTEND_DIR)/dist $(BACKEND_DIR)/static

serve:
	cd $(BACKEND_DIR) && $(VENV)/bin/uvicorn app.main:app --host 127.0.0.1 --port 8400

lint:
	cd $(BACKEND_DIR) && $(VENV)/bin/ruff check app/ tests/
	cd $(FRONTEND_DIR) && npm run lint

# Idea Generator Monorepo

This repository contains a small monorepo for the Idea Generator app:

- `packages/client`: React + TypeScript + Vite frontend
- `packages/server`: FastAPI + Pydantic backend backed by SQLite

The root workspace uses Bun to install JavaScript dependencies and to run both apps together in development.

## Prerequisites

- Bun `1.3+`
- Python `3.11+`

## Repository structure

```text
.
├── package.json           # Bun workspace and root scripts
├── index.ts               # starts client + server concurrently
├── packages/
│   ├── client/            # React app
│   └── server/            # FastAPI service
└── README.md
```

## Initial setup

Install workspace dependencies:

```bash
bun install
```

Set up the Python virtual environment for the server:

```bash
cd packages/server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then update `packages/server/.env` with valid values such as:

- `OPENROUTER_API_KEY`
- `API_SECRET_KEY`

## Run the full app locally

From the repo root:

```bash
bun run dev
```

This starts:

- frontend on `http://localhost:3000`
- backend on `http://localhost:8000`

The client dev server proxies `/api` requests to the FastAPI server.

## Run each package individually

### Client

```bash
cd packages/client
bun run dev
```

### Server

```bash
cd packages/server
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

## Common commands

### Root

```bash
bun run dev
bun run format
```

### Client

```bash
cd packages/client
bun run dev
bun run build
bun run lint
bun run preview
```

### Server

```bash
cd packages/server
./.venv/bin/python -m unittest tests.test_app -v
```

## API docs

When the server is running, FastAPI exposes:

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

For backend-specific details, see `packages/server/README.md`.
For frontend-specific details, see `packages/client/README.md`.
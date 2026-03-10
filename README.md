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

## Docker and Railway

The repo includes separate Dockerfiles for each Railway service:

- client: `packages/client/Dockerfile`
- server: `packages/server/Dockerfile`

### Client service

Build and run locally:

```bash
docker build -f packages/client/Dockerfile -t idea-generator-client .
docker run --rm -p 3000:3000 -e BACKEND_URL=http://host.docker.internal:8000 idea-generator-client
```

The client container serves the built SPA and proxies `/api/*` to `BACKEND_URL`.

### Server service

Build and run locally:

```bash
docker build -f packages/server/Dockerfile -t idea-generator-server .
docker run --rm -p 8000:8000 \
  -e OPENROUTER_API_KEY=your-key \
  -e API_SECRET_KEY=your-secret \
  idea-generator-server
```

### Railway setup

Create two Railway services from this repo:

1. **server service**
   - keep the service root at the repo root so Docker can use the full monorepo context
   - Dockerfile path: `packages/server/Dockerfile`
   - required envs: `OPENROUTER_API_KEY`, `API_SECRET_KEY`
   - optional envs: `IDEAS_DB_PATH`, `ALLOWED_ORIGINS`, `OPENROUTER_MODEL`, `OPENROUTER_TEMPERATURE`, `OUTPUT_NUMBER`
   - attach a volume and set `IDEAS_DB_PATH=/data/ideas.db` if you want SQLite persistence
2. **client service**
   - keep the service root at the repo root so Bun workspace files are available during the image build
   - Dockerfile path: `packages/client/Dockerfile`
   - required env: `BACKEND_URL=https://<your-server-domain>`

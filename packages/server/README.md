# Idea Generator API

FastAPI service for generating and storing idea suggestions.

## What it does

- accepts structured input from the frontend
- validates request and response payloads with Pydantic
- generates exactly 5 project ideas through OpenRouter
- caches duplicate requests by input
- stores requests, outputs, model info, and token usage in SQLite
- protects API routes with the `X-API-Key` header

## Tech stack

- FastAPI
- Pydantic v2
- aiosqlite
- httpx
- SQLite

## Local setup

From `packages/server`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Update `.env` with real values before starting the server.

## Environment variables

- `OPENROUTER_API_KEY`: backend secret used to call OpenRouter
- `API_SECRET_KEY`: shared secret expected in `X-API-Key`
- `OPENROUTER_MODEL` _(optional)_: defaults to `openai/gpt-4o-mini`
- `OPENROUTER_TEMPERATURE` _(optional)_: defaults to `0.9`
- `IDEAS_DB_PATH` _(optional)_: defaults to `ideas.db`
- `IDEAS_CACHE_TTL_DAYS` _(optional)_: limits cache hits to recent entries only
- `OUTPUT_NUMBER` _(optional)_: default number of ideas to generate when the request does not provide `number_of_ideas`
- `ALLOWED_ORIGINS` _(optional)_: comma-separated browser origins allowed to call the API

## Run locally

From `packages/server`:

```bash
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

The monorepo root also provides a combined dev command:

```bash
cd ../..
bun run dev
```

## API docs

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

In Swagger, click **Authorize** and enter your `API_SECRET_KEY` value for `X-API-Key`.

## Routes

### Welcome

- `GET /api/`

Returns a basic welcome message used by the frontend health check.

### Generate ideas

- canonical route: `POST /api/`
- compatibility aliases: `POST /` and `POST /api/generate_idea`

Example request:

```bash
curl -X POST http://127.0.0.1:8000/api/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-frontend-secret" \
  -d '{
    "user_id": "user-1",
    "prompt_template": "Act as a creative product designer. Generate unique, catchy, and short project titles 6-10 words maximum). Do not include descriptions, punctuation, or "Project:" prefixes. Focus on punchy, memorable names.",
    "model": "openai/gpt-4o-mini",
    "temperature": 0.9,
    "number_of_ideas": 5,
    "metadata": {
      "What do you love": ["tech", "art"],
      "What does the world need": ["education"],
      "What are you good at": ["design", "coding"],
      "Extra information": ["I am a software engineer", "I am a designer"]
    }
  }'
```

Example response fields:

- `request_id`
- `user_id`
- `prompt_template`
- `metadata`
- `ideas`
- `usage.prompt_tokens`
- `usage.completion_tokens`
- `usage.total_tokens`
- `model`
- `created_at`

### Read saved requests

- `GET /requests`

```bash
curl http://127.0.0.1:8000/requests \
  -H "X-API-Key: your-frontend-secret"
```

Returns previously saved requests ordered from newest to oldest.

## Validation approach

The server uses Pydantic models in `models.py` for request and response validation, including:

- `IdeaGenerationRequest`
- `IdeaGenerationResponse`
- `StoredIdeaRequest`
- `TokenUsage`

FastAPI validates incoming JSON against these models before route logic executes.

## Project structure

```text
packages/server/
├── main.py          # FastAPI app setup, middleware, router mounting
├── routers.py       # HTTP routes
├── auth.py          # API key dependency
├── db.py            # SQLite initialization and queries
├── models.py        # Pydantic request/response models
├── services.py      # OpenRouter integration and response normalization
├── tests/
│   └── test_app.py  # API tests
├── requirements.txt
├── run.sh           # local helper used by the root dev command
└── README.md
```

## Tests

Run the current server test suite with:

```bash
./.venv/bin/python -m unittest tests.test_app -v
```

## Deploy to Railway

The service uses a local SQLite file by default, so a separate database service is not required.

The repo includes a Dockerfile for Railway at `packages/server/Dockerfile`.

Because Railway containers are ephemeral, use a volume if you want persisted data:

1. create a volume mounted at a directory such as `/data`
2. set `IDEAS_DB_PATH=/data/ideas.db`
3. set `OPENROUTER_API_KEY` and `API_SECRET_KEY`
4. deploy with Dockerfile path: `packages/server/Dockerfile`

If persistence is not needed, you can keep the default `ideas.db` path inside the container.

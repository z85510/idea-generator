# Idea Generator API

FastAPI service that:

- accepts structured metadata from the frontend
- generates **exactly 5 project ideas**
- stores request input, output, model, and token usage in SQLite
- protects endpoints with an API key header

## Environment variables

- `OPENROUTER_API_KEY`: secret used by the backend to call OpenRouter
- `API_SECRET_KEY`: shared secret the frontend sends in `X-API-Key`
- `OPENROUTER_MODEL` _(optional)_: defaults to `openai/gpt-4o-mini`
- `IDEAS_DB_PATH` _(optional)_: defaults to `ideas.db`
- `ALLOWED_ORIGINS` _(optional)_: comma-separated browser origins that can call the API (e.g. `https://siif.ai,https://app.siift.ai,https://beta.siift.ai`). Requests with an `Origin` header not in this list get 403. If unset or empty, no origin restriction is applied.

## Deploy to Railway

You **don’t need to create a separate database**. The app uses a single **SQLite file** (e.g. `ideas.db`). No PostgreSQL or MySQL setup.

**Important:** On Railway the container filesystem is **ephemeral**—on redeploy the file is reset and data is lost. To keep data:

1. In your Railway project, add a **Volume** and set the **mount path to a directory**, e.g. `/data` (not `/ideas.db`—the mount path must be a directory; the DB file goes inside it).
2. In **Variables**, set `IDEAS_DB_PATH=/data/ideas.db` so the SQLite file lives inside that volume.

If you’re fine losing ideas on each deploy (e.g. dev only), you can skip the volume and leave `IDEAS_DB_PATH` unset (defaults to `ideas.db` in the container).

**Steps:**

1. [Railway](https://railway.app) → **New Project** → **Deploy from GitHub** → select this repo and branch (e.g. `dev`).
2. **Variables**: set `OPENROUTER_API_KEY`, `API_SECRET_KEY`. Optionally `OPENROUTER_MODEL`. If you added a volume, set `IDEAS_DB_PATH=/data/ideas.db`.
3. **Volume** (recommended): create a volume, mount path `/data`.
4. **Start command** (in Railway → Settings): `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Deploy; use the generated URL for your API.

## Run locally

```bash
cp .env.example .env

# then update .env with your real values
export OPENROUTER_API_KEY="your-openrouter-key"
export API_SECRET_KEY="your-frontend-secret"
./.venv/bin/python -m uvicorn main:app --reload
```

## Swagger UI

- Swagger: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

In Swagger, click **Authorize** and enter your `API_SECRET_KEY` value for `X-API-Key`.

## Generate ideas

`POST /`

```bash
curl -X POST http://127.0.0.1:8000/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-frontend-secret" \
  -d '{
    "user_id": "user-1",
    "metadata": {
      "What do you love": ["tech", "art"],
      "What does the world need": ["test"],
      "What are you good at": ["test"],
      "Extra information": ["I am a software engineer", "I am a designer"]
    }
  }'
```

Example response fields:

- `request_id`
- `ideas` (5 items)
- `usage.prompt_tokens`
- `usage.completion_tokens`
- `usage.total_tokens`
- `model`
- `created_at`

## Read saved requests

`GET /requests`

```bash
curl http://127.0.0.1:8000/requests \
  -H "X-API-Key: your-frontend-secret"
```

Returns saved request metadata, generated ideas, usage, and timestamps.

## Project structure

```
idea-generator/
├── main.py          # FastAPI app, lifespan, router mount
├── routers.py       # API routes (POST /, GET /requests)
├── auth.py          # API key dependency
├── db.py            # SQLite init, get_db, save/list ideas
├── models.py        # Pydantic request/response models
├── services.py      # OpenRouter idea generation
├── requirements.txt
├── tests/
│   └── test_app.py  # API and auth tests
├── .env.example
└── README.md
```

Run from project root so imports resolve. When you add more domains (e.g. users, admin), consider moving routes into `routers/` (e.g. `routers/ideas.py`) or an `app/` package.

## Tests

```bash
.venv/bin/python -m unittest tests.test_app -v
```

## CI

Tests run on GitHub Actions when you **push to `dev`** or open a **pull request targeting `dev`**. Workflow: [`.github/workflows/test.yml`](.github/workflows/test.yml).

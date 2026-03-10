import os
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


API_HEADERS = {"X-API-Key": "frontend-secret"}


class MockResponse:
    def __init__(self, request_payload: dict | None = None) -> None:
        self.request_payload = request_payload or {}

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        requested_model = self.request_payload.get("model", "openai/gpt-4o-mini")
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "ideas": [
                                    "An AI co-founder coach for first-time builders.",
                                    "A platform matching artists with emerging tech startups.",
                                    "A community app for testing social-impact project concepts.",
                                    "A skill-sharing marketplace for people building meaningful tools.",
                                    "A research dashboard that maps personal skills to market needs.",
                                    "A solo-founder CRM for tracking early customer interviews.",
                                    "A micro-learning app for career transitions into design.",
                                    "A founder wellness planner for burnout prevention.",
                                    "A local community marketplace for circular economy products.",
                                    "A product validation tool for mission-driven startups.",
                                ]
                            }
                        ),
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 120,
                "completion_tokens": 180,
                "total_tokens": 300,
            },
            "model": requested_model,
        }


class MockAsyncClient:
    last_payload: dict | None = None
    call_count = 0

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs) -> MockResponse:
        type(self).call_count += 1
        type(self).last_payload = kwargs.get("json")
        return MockResponse(type(self).last_payload)


class IdeaGeneratorAppTests(unittest.TestCase):
    def setUp(self) -> None:
        MockAsyncClient.last_payload = None
        MockAsyncClient.call_count = 0

    def test_generate_idea_persists_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = os.path.join(temp_dir, "test_ideas.db")
            with patch.dict(
                os.environ,
                {
                    "IDEAS_DB_PATH": database_path,
                    "API_SECRET_KEY": API_HEADERS["X-API-Key"],
                    "OPENROUTER_API_KEY": "test-key",
                },
                clear=False,
            ):
                with patch("services.httpx.AsyncClient", MockAsyncClient):
                    with TestClient(app) as client:
                        response = client.post(
                            "/",
                            json={
                                "user_id": "user-1",
                                "prompt_template": "You generate practical and creative project ideas.",
                                "metadata": {
                                    "What do you love": ["tech", "art"],
                                    "What does the world need": ["test"],
                                    "What are you good at": ["test"],
                                    "Extra information": ["I am a software engineer", "I am a designer"],
                                },
                            },
                            headers=API_HEADERS,
                        )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["user_id"], "user-1")
            self.assertEqual(len(payload["ideas"]), 5)
            self.assertEqual(payload["usage"]["total_tokens"], 300)

            connection = sqlite3.connect(database_path)
            try:
                row = connection.execute(
                    "SELECT user_id, metadata, ideas, total_tokens FROM idea_requests"
                ).fetchone()
            finally:
                connection.close()

            self.assertEqual(
                (
                    row[0],
                    json.loads(row[1]),
                    json.loads(row[2]),
                    row[3],
                ),
                (
                    "user-1",
                    {
                        "What do you love": ["tech", "art"],
                        "What does the world need": ["test"],
                        "What are you good at": ["test"],
                        "Extra information": ["I am a software engineer", "I am a designer"],
                    },
                    payload["ideas"],
                    300,
                ),
            )

    def test_get_requests_returns_saved_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = os.path.join(temp_dir, "history_ideas.db")
            with patch.dict(
                os.environ,
                {
                    "IDEAS_DB_PATH": database_path,
                    "API_SECRET_KEY": API_HEADERS["X-API-Key"],
                    "OPENROUTER_API_KEY": "test-key",
                },
                clear=False,
            ):
                with patch("services.httpx.AsyncClient", MockAsyncClient):
                    with TestClient(app) as client:
                        create_response = client.post(
                            "/",
                            json={
                                "user_id": "user-2",
                                "prompt_template": "You generate practical and creative project ideas.",
                                "metadata": {
                                    "What do you love": ["design"],
                                    "What does the world need": ["education"],
                                    "What are you good at": ["teaching"],
                                },
                            },
                            headers=API_HEADERS,
                        )
                        self.assertEqual(create_response.status_code, 200)

                        history_response = client.get("/requests", headers=API_HEADERS)

            self.assertEqual(history_response.status_code, 200)
            history_payload = history_response.json()
            self.assertEqual(len(history_payload), 1)
            self.assertEqual(history_payload[0]["user_id"], "user-2")
            self.assertEqual(history_payload[0]["usage"]["prompt_tokens"], 120)

    def test_generate_idea_uses_request_generation_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = os.path.join(temp_dir, "override_ideas.db")
            with patch.dict(
                os.environ,
                {
                    "IDEAS_DB_PATH": database_path,
                    "API_SECRET_KEY": API_HEADERS["X-API-Key"],
                    "OPENROUTER_API_KEY": "test-key",
                    "OPENROUTER_MODEL": "openai/gpt-4o-mini",
                    "OPENROUTER_TEMPERATURE": "0.9",
                    "OUTPUT_NUMBER": "5",
                },
                clear=False,
            ):
                with patch("services.httpx.AsyncClient", MockAsyncClient):
                    with TestClient(app) as client:
                        response = client.post(
                            "/",
                            json={
                                "user_id": "user-override",
                                "prompt_template": "You generate practical and creative project ideas.",
                                "metadata": {
                                    "What do you love": ["tech"],
                                    "What does the world need": ["education"],
                                },
                                "model": "anthropic/claude-haiku-4.5",
                                "temperature": 0.4,
                                "number_of_ideas": 3,
                            },
                            headers=API_HEADERS,
                        )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(len(payload["ideas"]), 3)
            self.assertEqual(payload["model"], "anthropic/claude-haiku-4.5")
            self.assertEqual(MockAsyncClient.last_payload["model"], "anthropic/claude-haiku-4.5")
            self.assertEqual(MockAsyncClient.last_payload["temperature"], 0.4)

    def test_generation_overrides_create_distinct_cache_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = os.path.join(temp_dir, "cache_options_ideas.db")
            with patch.dict(
                os.environ,
                {
                    "IDEAS_DB_PATH": database_path,
                    "API_SECRET_KEY": API_HEADERS["X-API-Key"],
                    "OPENROUTER_API_KEY": "test-key",
                },
                clear=False,
            ):
                with patch("services.httpx.AsyncClient", MockAsyncClient):
                    with TestClient(app) as client:
                        base_payload = {
                            "user_id": "user-cache",
                            "prompt_template": "You generate practical and creative project ideas.",
                            "metadata": {
                                "What do you love": ["design"],
                                "What does the world need": ["education"],
                            },
                        }
                        default_response = client.post("/", json=base_payload, headers=API_HEADERS)
                        override_response = client.post(
                            "/",
                            json={**base_payload, "number_of_ideas": 3},
                            headers=API_HEADERS,
                        )

            self.assertEqual(default_response.status_code, 200)
            self.assertEqual(override_response.status_code, 200)
            self.assertEqual(MockAsyncClient.call_count, 2)

            connection = sqlite3.connect(database_path)
            try:
                rows = connection.execute("SELECT id FROM idea_requests").fetchall()
            finally:
                connection.close()
            self.assertEqual(len(rows), 2, "different generation overrides should not share cache")

    def test_requests_are_rejected_without_valid_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = os.path.join(temp_dir, "secure_ideas.db")
            with patch.dict(
                os.environ,
                {
                    "IDEAS_DB_PATH": database_path,
                    "API_SECRET_KEY": API_HEADERS["X-API-Key"],
                    "OPENROUTER_API_KEY": "test-key",
                },
                clear=False,
            ):
                with TestClient(app) as client:
                    post_response = client.post(
                        "/",
                        json={
                            "user_id": "user-3",
                            "prompt_template": "You generate practical and creative project ideas.",
                            "metadata": {"What do you love": ["tech"], "What does the world need": ["test"], "What are you good at": ["test"], "Extra information": ["I am a software engineer", "I am a designer"]},
                        },
                    )
                    get_response = client.get(
                        "/requests",
                        headers={"X-API-Key": "wrong-key"},
                    )

            self.assertEqual(post_response.status_code, 403)
            self.assertEqual(get_response.status_code, 403)

    def test_same_input_returns_cached_result_without_calling_llm(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = os.path.join(temp_dir, "cache_ideas.db")
            with patch.dict(
                os.environ,
                {
                    "IDEAS_DB_PATH": database_path,
                    "API_SECRET_KEY": API_HEADERS["X-API-Key"],
                    "OPENROUTER_API_KEY": "test-key",
                },
                clear=False,
            ):
                with patch("services.httpx.AsyncClient", MockAsyncClient):
                    with TestClient(app) as client:
                        metadata = {
                            "What do you love": ["design"],
                            "What does the world need": ["education"],
                            "What are you good at": ["teaching"],
                        }
                        payload = {"user_id": "user-a", "prompt_template": "You generate practical and creative project ideas.", "metadata": metadata}
                        r1 = client.post("/", json=payload, headers=API_HEADERS)
                        r2 = client.post(
                            "/",
                            json={"user_id": "user-b", "prompt_template": "You generate practical and creative project ideas.", "metadata": metadata},
                            headers=API_HEADERS,
                        )

            self.assertEqual(r1.status_code, 200)
            self.assertEqual(r2.status_code, 200)
            self.assertEqual(r1.json()["request_id"], r2.json()["request_id"])
            self.assertEqual(r1.json()["ideas"], r2.json()["ideas"])
            self.assertEqual(r2.json()["user_id"], "user-b", "response uses current request user_id")

            connection = sqlite3.connect(database_path)
            try:
                rows = connection.execute("SELECT id FROM idea_requests").fetchall()
            finally:
                connection.close()
            self.assertEqual(len(rows), 1, "should store only one row for same metadata")

    def test_requests_with_disallowed_origin_are_rejected(self) -> None:
        with patch.dict(
            os.environ,
            {"ALLOWED_ORIGINS": "http://localhost:3000,http://localhost:3001"},
            clear=False,
        ):
            from importlib import reload
            import main as main_mod
            reload(main_mod)
            test_app = main_mod.app
        with TestClient(test_app) as client:
            r = client.post(
                "/",
                json={"user_id": "u", "prompt_template": "You generate ideas.", "metadata": {"x": ["y"]}},
                headers={**API_HEADERS, "Origin": "https://evil.com"},
            )
        self.assertEqual(r.status_code, 403)
        self.assertIn("Origin not allowed", r.json()["detail"])


if __name__ == "__main__":
    unittest.main()

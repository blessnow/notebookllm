import asyncio
import json

from fastapi.testclient import TestClient

from app.main import app


def test_fastapi_app_is_asgi_callable() -> None:
    assert callable(app)

    messages: list[dict] = []

    async def receive() -> dict:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict) -> None:
        messages.append(message)

    scope = {"type": "http", "method": "GET", "path": "/healthz"}
    asyncio.run(app(scope, receive, send))

    body_msg = [m for m in messages if m["type"] == "http.response.body"][0]
    payload = json.loads(body_msg["body"].decode("utf-8"))
    assert payload["status"] == "ok"


def test_invalid_document_payload_returns_422() -> None:
    client = TestClient(app)

    notebook_res = client.post("/api/notebooks", json={"name": "Validation"})
    notebook_id = notebook_res.json()["id"]

    res = client.post(
        "/api/documents",
        json={
            "notebook_id": notebook_id,
            "title": "Invalid",
            "source_type": "text",
        },
    )

    assert res.status_code == 422
    assert "Either content or source_uri must be provided." in res.json()["detail"]

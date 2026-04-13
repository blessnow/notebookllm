from fastapi.testclient import TestClient

from app.api.routes import repo
from app.main import app


client = TestClient(app)


def setup_function() -> None:
    repo.reset()


def test_notebook_document_chat_flow() -> None:
    notebook_res = client.post("/api/notebooks", json={"name": "AI Research"})
    assert notebook_res.status_code == 200
    notebook_id = notebook_res.json()["id"]

    doc_res = client.post(
        "/api/documents",
        json={
            "notebook_id": notebook_id,
            "title": "NotebookLM intro",
            "source_type": "url",
            "source_uri": "https://example.com/notebooklm",
            "content": "NotebookLM lets users upload private materials and ask grounded questions with citations.",
        },
    )
    assert doc_res.status_code == 200

    list_doc_res = client.get(f"/api/notebooks/{notebook_id}/documents")
    assert list_doc_res.status_code == 200
    assert len(list_doc_res.json()) == 1

    chat_res = client.post(
        "/api/chat",
        json={"notebook_id": notebook_id, "question": "NotebookLM 的价值是什么？", "top_k": 5},
    )
    assert chat_res.status_code == 200
    body = chat_res.json()
    assert "answer" in body
    assert len(body["citations"]) >= 1
    assert body["citations"][0]["start_offset"] >= 0
    assert body["citations"][0]["end_offset"] > body["citations"][0]["start_offset"]


def test_chat_returns_dont_know_without_docs() -> None:
    notebook_res = client.post("/api/notebooks", json={"name": "Empty"})
    notebook_id = notebook_res.json()["id"]

    chat_res = client.post(
        "/api/chat",
        json={"notebook_id": notebook_id, "question": "没有文档时会怎样？", "top_k": 5},
    )

    assert chat_res.status_code == 200
    assert chat_res.json()["answer"].startswith("不知道")
    assert chat_res.json()["citations"] == []


def test_text_file_ingestion_via_source_uri(tmp_path) -> None:
    notebook_res = client.post("/api/notebooks", json={"name": "File Notebook"})
    notebook_id = notebook_res.json()["id"]

    file_path = tmp_path / "sample.txt"
    file_path.write_text(
        "NotebookLM can read your files, chunk content, retrieve relevant spans and attach citations.",
        encoding="utf-8",
    )

    doc_res = client.post(
        "/api/documents",
        json={
            "notebook_id": notebook_id,
            "title": "sample.txt",
            "source_type": "text",
            "source_uri": str(file_path),
        },
    )
    assert doc_res.status_code == 200
    assert doc_res.json()["status"] == "done"

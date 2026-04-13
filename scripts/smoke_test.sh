#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

NOTEBOOK_ID=$(curl -sS -X POST "$BASE_URL/api/notebooks" \
  -H 'content-type: application/json' \
  -d '{"name":"smoke-notebook"}' | python -c 'import sys, json; print(json.load(sys.stdin)["id"])')

curl -sS -X POST "$BASE_URL/api/documents" \
  -H 'content-type: application/json' \
  -d "{\"notebook_id\":\"$NOTEBOOK_ID\",\"title\":\"smoke-doc\",\"source_type\":\"text\",\"source_uri\":\"inline\",\"content\":\"NotebookLM style retrieval uses chunks, hybrid search, reranking and citation mapping for grounded answers.\"}" >/dev/null

CHAT_JSON=$(curl -sS -X POST "$BASE_URL/api/chat" \
  -H 'content-type: application/json' \
  -d "{\"notebook_id\":\"$NOTEBOOK_ID\",\"question\":\"test?\",\"top_k\":5}")

python - <<'PY' "$CHAT_JSON"
import json
import sys

body = json.loads(sys.argv[1])
assert "answer" in body and body["answer"], "missing answer"
assert isinstance(body.get("citations"), list), "citations not list"
assert len(body["citations"]) >= 1, "citations should not be empty"
print("Smoke test passed.")
PY

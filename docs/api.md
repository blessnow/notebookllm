# API 草案

## POST /api/notebooks
创建笔记本。

## GET /api/notebooks
查询笔记本列表。

## POST /api/documents
登记文档并执行真实 ingestion：清洗、chunk、索引。

请求体支持：

- `content`（直接文本）
- 或 `source_uri`（文件路径）
- `source_type` 可为 `text/pdf/doc/url/youtube`

## GET /api/notebooks/{notebook_id}/documents
按 notebook 查看文档。

## POST /api/chat
请求体：

```json
{
  "notebook_id": "...",
  "question": "NotebookLM 的核心价值是什么？",
  "top_k": 5
}
```

返回体：

```json
{
  "answer": "...[1]\\n...[2]",
  "citations": [
    {
      "id": 1,
      "doc_id": "...",
      "chunk_id": "...",
      "snippet": "...",
      "start_offset": 0,
      "end_offset": 120
    }
  ]
}
```

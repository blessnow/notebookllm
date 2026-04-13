# NotebookLLM (MVP Scaffold)

一个用于复刻 NotebookLM 核心能力的最小可运行后端骨架：

- 文档入库（上传元数据）
- 多文件类型解析（PDF / 网页 / YouTube / docx / text）
- 文档分块与索引（ingestion pipeline）
- RAG 问答接口（hybrid retrieval + rerank）
- 引用结构化返回（含 offset 映射）

## 快速启动

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

打开 `http://127.0.0.1:8000/docs` 查看 Swagger。

> 说明：仓库内含轻量 `fastapi` / `pydantic` 兼容层，便于离线 CI 环境执行测试。

## 测试与验证

```bash
pytest -q
```

完整步骤见 `TESTING.md`（含手工验证与 smoke test）。

## 目录结构

- `app/main.py`: FastAPI 入口
- `app/api/routes.py`: HTTP 路由
- `app/services/`: 业务层（Notebook/Document/RAG）
- `app/core/models.py`: Pydantic 模型
- `docs/architecture.md`: 系统架构说明
- `docs/api.md`: API 设计草案

## 下一步

1. 把 `InMemoryRepository` 替换为 Postgres + Redis。
2. 将检索层替换为向量库（pgvector/Weaviate）与专用 reranker。
3. 将答案生成从抽取式升级为 LLM 生成式并保留 citation 对齐。

## 当前支持的文档输入

- `source_type=text`: 直接 `content` 或 `source_uri` 指向 `.txt`
- `source_type=pdf`: `source_uri` 指向本地 `.pdf`（pdfplumber / pymupdf）
- `source_type=doc`: `source_uri` 指向本地 `.docx`
- `source_type=url`: `source_uri` 指向网页 URL（BeautifulSoup 提取正文）
- `source_type=youtube`: `source_uri` 指向 YouTube URL（transcript API）

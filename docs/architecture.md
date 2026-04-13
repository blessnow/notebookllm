# NotebookLLM 架构（MVP -> Production）

## 1) 分层

- Frontend: Web UI（notebook、文档、聊天、引用面板）
- API: FastAPI
- App Services: Notebook、Document、Chat、AI Orchestrator
- RAG Engine: Retriever + Reranker + Context Builder
- Storage: Postgres + Object Storage + Vector DB

## 2) 关键流水线

### Ingestion
1. 上传文件到对象存储
2. 解析文本（PDF/URL/字幕）
3. 语义切块（800/120）
4. embedding 入向量库
5. metadata 写入 Postgres

### Q&A
1. query embedding
2. hybrid retrieval（vector + BM25）
3. rerank topN
4. context packing（token budget）
5. llm generation（强约束 + 引用）

## 3) 可靠性建议

- 异步任务队列处理 indexing
- 每个 notebook 独立权限域
- 统一观测：retrieval 命中率、引用准确率、幻觉率

## 4) 当前仓库已实现（v0.2）

- Ingestion: 文档创建时执行语义分块（chunk + overlap）并入内存索引。
- Parser: 支持 PDF（pdfplumber/pymupdf）、网页（BeautifulSoup）、YouTube transcript、text/docx 解析。
- Retrieval: TF-IDF cosine + BM25 混合召回（hybrid retrieval）。
- Rerank: 基于 query-term overlap + 近邻命中加权重排。
- Citation Mapping: 返回 chunk 级 citation，含 `chunk_id/start_offset/end_offset`。

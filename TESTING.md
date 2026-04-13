# 如何测试 / 如何验证

下面给你一套可直接执行的验证清单（本地开发机）。

## 1) 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 2) 自动化测试（推荐先跑）

```bash
pytest -q
```

你应看到：
- healthz 测试通过
- API 主流程（notebook -> document -> chat）通过
- 无文档场景返回“不知道”通过

## 3) 启动服务做手工验证

```bash
uvicorn app.main:app --reload
```

打开 Swagger：

- `http://127.0.0.1:8000/docs`

按顺序手工点这几个接口：

1. `POST /api/notebooks`
2. `POST /api/documents`
3. `GET /api/notebooks/{id}/documents`
4. `POST /api/chat`

你要重点验证：
- chat 返回 `answer`
- `citations` 数组非空（有文档时）
- 无文档时返回 `不知道...` 且 citations 为空

### 多文件类型验证（新增）

你可以在 `POST /api/documents` 分别测试：

- `source_type=text` + `content`
- `source_type=pdf` + `source_uri=/absolute/path/to/file.pdf`
- `source_type=doc` + `source_uri=/absolute/path/to/file.docx`
- `source_type=url` + `source_uri=https://example.com/article`
- `source_type=youtube` + `source_uri=https://www.youtube.com/watch?v=...`

## 4) 命令行 smoke test（可选）

服务启动后执行：

```bash
bash scripts/smoke_test.sh
```

看到 `Smoke test passed.` 即表示主流程可用。

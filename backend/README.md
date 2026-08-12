# MD2Blog Backend

FastAPI 기반의 MD2Blog API 서버입니다.

## 로컬 실행

```shell
uv sync
uv run uvicorn md2blog.main:app --reload
```

API 상태는 `http://localhost:8000/health`에서 확인할 수 있습니다.

## 검사

```shell
uv run pytest
uv run ruff check .
uv run mypy
```

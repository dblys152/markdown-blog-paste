# MD2Blog Backend

FastAPI 기반의 MD2Blog API 서버입니다.

## 로컬 실행

```shell
cp .env.example .env.local
uv sync
uv run uvicorn md2blog.main:app --reload
```

애플리케이션 상태는 `http://localhost:8000/health`, 데이터베이스 연결 상태는
`http://localhost:8000/health/database`에서 확인할 수 있습니다.

## 검사

```shell
uv run pytest
uv run ruff check .
uv run mypy
```

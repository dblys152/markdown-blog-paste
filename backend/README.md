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

회원가입 인증 메일은 Gmail SMTP로 발송합니다. `.env.example`의 SMTP 및
이메일 인증 정책 변수를 `.env.local` 또는 배포 환경의 Secret/환경 변수로 설정해야 합니다.

애플리케이션 내부 Scheduler는 Outbox를 5초마다 처리하고, 매일 만료된 휴지통 페이지를
정리합니다. 프로세스 시작 시 두 작업을 즉시 실행해 비활성 기간에 놓친 작업을 보완합니다.

새 마이그레이션은 배포 전에 운영 데이터베이스에 직접 실행합니다.

```shell
uv run alembic upgrade head
```

## 검사

```shell
uv run pytest
uv run ruff check .
uv run mypy
```

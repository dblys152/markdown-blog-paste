# markdown-blog-paste

Markdown 문서를 블로그 에디터에 붙여넣기 좋은 HTML로 변환하는 도구입니다.

## Web App

```bash
npm install
npm run dev
```

개발 서버가 실행되면 브라우저에서 `http://127.0.0.1:5173/`을 열어 사용합니다.

지원 모드:

| 모드 | 설명 |
|---|---|
| 기본 변환 | Markdown을 기본 HTML로 변환합니다. |
| 빈 줄 추가 | 블로그 에디터에서 문단 간격이 유지되도록 빈 줄을 추가합니다. |
| 네이버 블로그용 | 네이버 에디터에 맞게 코드블록과 빈 줄 처리를 보정합니다. |

## Python CLI

기존 CLI 도구는 `python-cli/` 디렉터리에 있습니다.

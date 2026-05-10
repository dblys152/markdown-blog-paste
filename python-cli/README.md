# Python CLI

Markdown 파일을 HTML로 변환하는 Python CLI 도구입니다.

이 도구는 Markdown으로 작성한 글을 브라우저에서 미리보기 하거나, 티스토리와 네이버 블로그 같은 에디터에 붙여넣기 좋은 형태로 변환하기 위해 사용합니다.

## 지원 변환 방식

현재 Python CLI는 3가지 변환 방식을 제공합니다.

| 파일 | 설명 |
|---|---|
| `convert.py` | Markdown을 기본 HTML로 변환합니다. |
| `convert_blank_lines.py` | Markdown을 HTML로 변환한 뒤, 블로그 에디터에서 문단 간격이 유지되도록 빈 줄을 추가합니다. |
| `convert_for_naver.py` | 네이버 블로그에 붙여넣기 좋도록 코드블록과 빈 줄 처리를 보정합니다. |

## 설치

Python 3 환경이 필요합니다.

```bash
python3 --version

import re
import sys
import html as html_lib
from pathlib import Path
from typing import Callable, Iterable

import markdown


# -----------------------------
# Common settings
# -----------------------------

MARKDOWN_EXTENSIONS = [
    "extra",
    "fenced_code",
    "tables",
    "nl2br",
]

OUTPUT_SUFFIX = ".html"
HTML_LANG = "ko"
HTML_CHARSET = "UTF-8"

EDITOR_SPACER = '<p class="editor-spacer">&nbsp;</p>'
CODE_BLOCK_SPACER_MARKER = "<!--EDITOR_SPACER_AFTER_CODE_BLOCK-->"

BLOCK_END_TAGS = (
    "</p>",
    "</blockquote>",
    "</pre>",
    "</table>",
    "</ul>",
    "</ol>",
)

HEADING_END_TAGS = (
    "</h2>",
    "</h3>",
)

BASE_CSS = """
body {
  font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
  line-height: 1.9;
  font-size: 16px;
  color: #222;
  max-width: 760px;
  margin: 40px auto;
  padding: 0 20px;
}

h1 {
  font-size: 28px;
  margin-top: 44px;
  margin-bottom: 24px;
  line-height: 1.4;
}

h2 {
  font-size: 24px;
  margin-top: 44px;
  margin-bottom: 20px;
  line-height: 1.4;
}

h3 {
  font-size: 20px;
  margin-top: 36px;
  margin-bottom: 16px;
  line-height: 1.5;
}

p {
  margin: 16px 0;
  line-height: 1.9;
}

ul,
ol {
  margin: 16px 0;
  padding-left: 28px;
}

li {
  margin: 8px 0;
  line-height: 1.8;
}

blockquote {
  margin: 24px 0;
  padding: 14px 18px;
  border-left: 4px solid #d1d5db;
  background: #f9fafb;
  color: #555;
}

pre {
  display: block;
  background: #f8f9fa;
  color: #111827;
  padding: 18px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  overflow-x: auto;
  line-height: 1.75;
  font-size: 15px;
  white-space: pre;
  margin: 24px 0;
}

pre code {
  display: block;
  background: transparent;
  color: #111827;
  font-family: Consolas, Monaco, "Courier New", monospace;
  font-size: 15px;
  line-height: 1.75;
  white-space: pre;
}

code {
  font-family: Consolas, Monaco, "Courier New", monospace;
}

p code,
li code {
  background: #f3f4f6;
  color: #d6336c;
  padding: 2px 5px;
  border-radius: 4px;
  font-size: 0.9em;
}

table {
  border-collapse: collapse;
  width: 100%;
  margin: 24px 0;
  font-size: 15px;
}

th,
td {
  border: 1px solid #ddd;
  padding: 10px 12px;
  line-height: 1.7;
}

th {
  background: #f5f5f5;
  font-weight: 700;
}

hr {
  border: 0;
  border-top: 1px solid #e5e7eb;
  margin: 36px 0;
}

.editor-spacer {
  font-size: 16px;
  line-height: 1.4;
  margin: 0;
}

img {
  max-width: 100%;
}
""".strip()

NAVER_CODE_BLOCK_STYLE = "".join(
    [
        "font-family: Consolas, Monaco, 'Courier New', monospace;",
        "font-size: 15px;",
        "line-height: 1.75;",
        "color: #111827;",
        "background-color: #f8f9fa;",
        "border: 1px solid #d1d5db;",
        "border-radius: 8px;",
        "padding: 18px;",
        "margin: 24px 0;",
        "white-space: normal;",
        "overflow-x: auto;",
    ]
)

PostProcessor = Callable[[str], str]


def render_base_markdown(markdown_text: str) -> str:
    """Markdown 문자열을 HTML 본문으로 변환합니다."""
    return markdown.markdown(
        markdown_text,
        extensions=MARKDOWN_EXTENSIONS,
        output_format="html5",
    )


def add_editor_blank_lines(html_text: str) -> str:
    """
    티스토리/네이버 같은 에디터에 붙여넣을 때 CSS margin이 사라져도
    문단 간격이 유지되도록 실제 빈 문단을 삽입합니다.

    완전히 빈 태그는 에디터가 제거할 수 있어 &nbsp;를 사용합니다.
    """
    for tag in BLOCK_END_TAGS:
        html_text = html_text.replace(tag, f"{tag}\n{EDITOR_SPACER}")

    # 제목 뒤 spacer는 마지막에 추가합니다.
    # 먼저 추가하면 spacer의 </p>에 다시 EDITOR_SPACER가 붙을 수 있습니다.
    for tag in HEADING_END_TAGS:
        html_text = html_text.replace(tag, f"{tag}\n{EDITOR_SPACER}")

    # 네이버용 코드블록 변환에서 marker를 사용한 경우 마지막에 실제 spacer로 교체합니다.
    html_text = html_text.replace(CODE_BLOCK_SPACER_MARKER, EDITOR_SPACER)

    return html_text


def preserve_code_spacing(code_text: str) -> str:
    """코드 내용의 줄바꿈과 들여쓰기를 HTML 복붙 후에도 유지되도록 변환합니다."""
    unescaped = html_lib.unescape(code_text).rstrip("\n")
    escaped = html_lib.escape(unescaped, quote=False)

    return (
        escaped
        .replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
        .replace(" ", "&nbsp;")
        .replace("\n", "<br>")
    )


def render_naver_code_block(match: re.Match[str]) -> str:
    """<pre><code> 블록을 네이버 복붙에 더 안정적인 div 기반 코드블록으로 변환합니다."""
    code_text = match.group(2)
    preserved_code = preserve_code_spacing(code_text)

    return (
        f'<div style="{NAVER_CODE_BLOCK_STYLE}">{preserved_code}</div>'
        f'\n{CODE_BLOCK_SPACER_MARKER}'
    )


def convert_code_blocks_for_naver(html_text: str) -> str:
    """
    네이버 블로그는 <pre><code>를 복붙할 때 테이블 셀처럼 만들거나,
    코드 내부 줄바꿈/공백을 무시하는 경우가 있어 div 기반 코드블록으로 바꿉니다.
    """
    code_block_pattern = re.compile(
        r'<pre><code(?: class="language-([^"]+)")?>(.*?)</code></pre>',
        re.DOTALL,
    )

    return code_block_pattern.sub(render_naver_code_block, html_text)


def render_markdown(markdown_text: str, post_processors: Iterable[PostProcessor] = ()) -> str:
    """Markdown을 HTML로 변환하고, 버전별 후처리를 순서대로 적용합니다."""
    body_html = render_base_markdown(markdown_text)

    for processor in post_processors:
        body_html = processor(body_html)

    return body_html


def wrap_html(body_html: str, title: str) -> str:
    """변환된 HTML 본문을 미리보기용 전체 HTML 문서로 감쌉니다."""
    safe_title = html_lib.escape(title, quote=True)

    return f"""<!DOCTYPE html>
<html lang="{HTML_LANG}">
<head>
  <meta charset="{HTML_CHARSET}" />
  <title>{safe_title}</title>
  <style>
{BASE_CSS}
  </style>
</head>
<body>
{body_html}
</body>
</html>
"""


def convert_file(input_path: Path, post_processors: Iterable[PostProcessor] = ()) -> Path:
    """Markdown 파일을 읽어 같은 위치에 HTML 파일로 저장합니다."""
    markdown_text = input_path.read_text(encoding="utf-8")
    body_html = render_markdown(markdown_text, post_processors)
    output_path = input_path.with_suffix(OUTPUT_SUFFIX)

    output_path.write_text(
        wrap_html(body_html, input_path.stem),
        encoding="utf-8",
    )

    return output_path


def run_cli(usage_message: str, post_processors: Iterable[PostProcessor] = ()) -> None:
    if len(sys.argv) < 2:
        print(usage_message)
        sys.exit(1)

    input_path = Path(sys.argv[1])

    if not input_path.exists():
        print(f"파일을 찾을 수 없습니다: {input_path}")
        sys.exit(1)

    output_path = convert_file(input_path, post_processors)
    print(f"변환 완료: {output_path}")

import { describe, expect, it } from "vitest";
import {
  addEditorBlankLines,
  applyBlogInlineStyles,
  CODE_BLOCK_SPACER_MARKER,
  convertCodeBlocksForNaver,
  EDITOR_SPACER,
} from "../../../src/shared/markdown/processors";

describe("applyBlogInlineStyles", () => {
  it("블로그 편집기에 필요한 제목과 표 스타일을 인라인으로 추가한다", () => {
    const html = applyBlogInlineStyles(
      '<h2 style="color: red">제목</h2><table><thead><tr><th>항목</th></tr></thead></table>',
    );
    const template = document.createElement("template");
    template.innerHTML = html;

    expect(template.content.querySelector("h2")?.getAttribute("style")).toContain("color: red");
    expect(template.content.querySelector("h2")?.getAttribute("style")).toContain("font-size: 24px");
    expect(template.content.querySelector("table")?.getAttribute("style")).toContain(
      "border-collapse: collapse",
    );
    expect(template.content.querySelector("th")?.getAttribute("style")).toContain(
      "background: #f5f5f5",
    );
  });
});

describe("addEditorBlankLines", () => {
  it("문단과 제목 뒤에 에디터용 빈 줄을 추가한다", () => {
    const html = addEditorBlankLines("<h2>제목</h2><p>본문</p>");

    expect(html).toBe(
      `<h2>제목</h2>\n${EDITOR_SPACER}<p>본문</p>\n${EDITOR_SPACER}`,
    );
  });

  it("코드블록 표시자를 에디터용 빈 줄로 교체한다", () => {
    expect(addEditorBlankLines(CODE_BLOCK_SPACER_MARKER)).toBe(EDITOR_SPACER);
  });
});

describe("convertCodeBlocksForNaver", () => {
  it("코드블록을 네이버용 div로 변환하고 공백과 줄바꿈을 보존한다", () => {
    const html = convertCodeBlocksForNaver(
      '<pre><code class="language-ts">const value = &lt;tag&gt;;\n  next();\n</code></pre>',
    );

    expect(html).toContain('<div style="font-family: Consolas');
    expect(html).toContain("const&nbsp;value&nbsp;=&nbsp;&lt;tag&gt;;<br>");
    expect(html).toContain("&nbsp;&nbsp;next();");
    expect(html).toContain(CODE_BLOCK_SPACER_MARKER);
    expect(html).not.toContain("<pre>");
  });

  it("일반 인라인 코드는 변경하지 않는다", () => {
    const html = "<p><code>value</code></p>";

    expect(convertCodeBlocksForNaver(html)).toBe(html);
  });
});

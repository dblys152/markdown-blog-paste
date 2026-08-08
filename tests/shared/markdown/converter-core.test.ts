import { describe, expect, it } from "vitest";
import { renderBaseMarkdown, wrapHtml } from "../../../src/shared/markdown/converter-core";

describe("renderBaseMarkdown", () => {
  it("GFM 표를 HTML 표로 변환한다", () => {
    const html = renderBaseMarkdown("| 이름 | 값 |\n| --- | --- |\n| MD2Blog | 1 |");

    expect(html).toContain("<table>");
    expect(html).toContain("<td>MD2Blog</td>");
  });

  it("일반 줄바꿈을 br 요소로 변환한다", () => {
    expect(renderBaseMarkdown("첫 번째 줄\n두 번째 줄")).toContain("첫 번째 줄<br>두 번째 줄");
  });

  it("Mermaid 코드블록의 언어 클래스를 유지한다", () => {
    const markdown = "```mermaid\ngraph TD\n  A --> B\n```";

    expect(renderBaseMarkdown(markdown)).toContain('class="language-mermaid"');
  });
});

describe("wrapHtml", () => {
  it("제목을 이스케이프하고 중복 목차 ID를 구분한다", () => {
    const html = wrapHtml("<h2>같은 제목</h2><h2>같은 제목</h2>", '<문서 "제목">');
    const document = new DOMParser().parseFromString(html, "text/html");
    const headings = Array.from(document.querySelectorAll("main h2"));
    const firstId = headings[0]?.id;

    expect(html).toContain("<title>&lt;문서 &quot;제목&quot;&gt;</title>");
    expect(firstId).toBeTruthy();
    expect(headings[1]?.id).toBe(`${firstId}-2`);
    expect(document.querySelector(`a[href="#${headings[1]?.id}"]`)).not.toBeNull();
  });

  it("목차 대상이 없으면 플로팅 내비게이션을 만들지 않는다", () => {
    const html = wrapHtml("<p>본문</p>", "문서");
    const document = new DOMParser().parseFromString(html, "text/html");

    expect(document.querySelector("aside.floating-section-nav")).toBeNull();
  });
});

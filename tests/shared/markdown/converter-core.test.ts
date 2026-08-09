import { describe, expect, it } from "vitest";
import { convertMarkdown, renderBaseMarkdown, wrapHtml } from "../../../src/shared/markdown/converter-core";

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

describe("convertMarkdown options", () => {
  it("H2만 목차에 포함한다", async () => {
    const result = await convertMarkdown("# 제목\n\n## 섹션 A\n\n### 하위 섹션\n\n## 섹션 B", "basic", "문서", {
      excludeFirstH1: false,
      generateH2Toc: true,
      addH2Dividers: false,
    });
    const document = new DOMParser().parseFromString(result.bodyHtml, "text/html");
    const links = Array.from(document.querySelectorAll(".h2-toc-item")).map((item) => item.textContent);

    expect(links).toEqual(["섹션 A", "섹션 B"]);
    expect(document.querySelector(".h2-toc-title")?.parentElement?.tagName).toBe("BODY");
    expect(document.querySelector("h2.h2-toc-title")?.textContent).toBe("목차");
    expect(document.querySelector("ol.h2-toc-list")).not.toBeNull();
    expect(document.querySelectorAll("li.h2-toc-item")).toHaveLength(2);
  });

  it("목차 자동 번호와 중복되지 않도록 H2의 기존 번호를 제거한다", async () => {
    const result = await convertMarkdown("## 1. 개요\n\n## 2) 설치", "basic", "문서", {
      excludeFirstH1: false,
      generateH2Toc: true,
      addH2Dividers: false,
    });
    const document = new DOMParser().parseFromString(result.bodyHtml, "text/html");

    expect(Array.from(document.querySelectorAll(".h2-toc-item")).map((item) => item.textContent)).toEqual(["개요", "설치"]);
    expect(document.querySelector(".h2-toc-list a")).toBeNull();
  });

  it("두 번째 H2부터 구분선을 추가한다", async () => {
    const result = await convertMarkdown("## 첫 번째\n\n내용\n\n## 두 번째\n\n내용\n\n## 세 번째", "basic", "문서", {
      excludeFirstH1: false,
      generateH2Toc: false,
      addH2Dividers: true,
    });
    const document = new DOMParser().parseFromString(result.bodyHtml, "text/html");

    expect(document.querySelectorAll("hr.h2-section-divider")).toHaveLength(2);
    expect(document.querySelector("h2:first-child")?.textContent).toBe("첫 번째");
  });

  it("목차와 구분선 옵션을 함께 사용하면 목차 아래에도 구분선을 추가한다", async () => {
    const result = await convertMarkdown("## 첫 번째\n\n내용\n\n## 두 번째", "basic", "문서", {
      excludeFirstH1: false,
      generateH2Toc: true,
      addH2Dividers: true,
    });
    const document = new DOMParser().parseFromString(result.bodyHtml, "text/html");

    expect(document.querySelector(".h2-toc-list + hr.h2-toc-divider + h2")?.textContent).toBe("첫 번째");
  });

  it.each(["blank-lines", "naver"] as const)("%s 모드에서 생성된 목차에도 빈 줄을 적용한다", async (mode) => {
    const result = await convertMarkdown("## 첫 번째\n\n본문\n\n## 두 번째", mode, "문서", {
      excludeFirstH1: false,
      generateH2Toc: true,
      addH2Dividers: false,
    });
    const document = new DOMParser().parseFromString(result.bodyHtml, "text/html");

    expect(document.querySelector("h2.h2-toc-title + p.editor-spacer")).not.toBeNull();
    expect(document.querySelector("ol.h2-toc-list + p.editor-spacer")).not.toBeNull();
  });

  it("첫 번째 H1만 결과에서 제외한다", async () => {
    const result = await convertMarkdown("# 문서 제목\n\n본문\n\n# 다른 H1", "basic", "문서", {
      excludeFirstH1: true,
      generateH2Toc: false,
      addH2Dividers: false,
    });
    const document = new DOMParser().parseFromString(result.bodyHtml, "text/html");

    expect(Array.from(document.querySelectorAll("h1")).map((heading) => heading.textContent)).toEqual(["다른 H1"]);
    expect(document.body.textContent).toContain("본문");
  });
});

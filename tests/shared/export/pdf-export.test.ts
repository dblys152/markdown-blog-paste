import { describe, expect, it } from "vitest";
import { createPrintableHtml } from "../../../src/shared/export/pdf-export";

describe("createPrintableHtml", () => {
  it("A4 인쇄 스타일과 원본 HTML로 인쇄 문서를 만든다", () => {
    const html = createPrintableHtml("<h1>제목</h1><table><tr><td>내용</td></tr></table>", "문서 <초안>");

    expect(html).toContain("<title>문서 &lt;초안&gt;</title>");
    expect(html).toContain("@page");
    expect(html).toContain("size: A4 portrait");
    expect(html).toContain("break-inside: avoid-page");
    expect(html).toContain('<article class="pdf-document"><h1>제목</h1>');
  });

  it("변환기가 추가한 화면용 레이아웃 스타일만 인쇄 문서에서 제거한다", () => {
    const html = createPrintableHtml(
      '<h1 style="color: red; font-size: 28px; margin-top: 44px; margin-bottom: 24px; line-height: 1.4">제목</h1>'
      + '<table style="border-collapse: collapse; width: 100%; margin: 24px 0; font-size: 15px">'
      + '<tr><td style="border: 1px solid #ddd; padding: 10px 12px; line-height: 1.7">내용</td></tr></table>',
      "문서",
    );
    const parsed = new DOMParser().parseFromString(html, "text/html");
    const heading = parsed.querySelector<HTMLElement>("h1");
    const table = parsed.querySelector<HTMLElement>("table");
    const cell = parsed.querySelector<HTMLElement>("td");

    expect(heading?.style.color).toBe("red");
    expect(heading?.style.fontSize).toBe("");
    expect(heading?.style.marginTop).toBe("");
    expect(table?.style.borderCollapse).toBe("collapse");
    expect(table?.style.width).toBe("100%");
    expect(table?.style.fontSize).toBe("");
    expect(table?.style.marginTop).toBe("");
    expect(cell?.style.border).toContain("1px solid");
    expect(cell?.style.padding).toBe("");
    expect(cell?.style.lineHeight).toBe("");
  });
});

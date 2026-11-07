import { describe, expect, it } from "vitest";
import { BASE_CSS, createBrowserPrintCss, createScopedContentCss } from "../../../src/shared/styles/styles";

describe("createScopedContentCss", () => {
  it("여러 줄 인라인 코드 박스를 줄마다 온전하게 렌더링한다", () => {
    const css = createScopedContentCss(".preview");

    expect(css).toContain(".preview td code");
    expect(css).toContain(".preview th code");
    expect(css).toContain("overflow-wrap: anywhere");
    expect(css).toContain("box-decoration-break: clone");
    expect(css).toContain("-webkit-box-decoration-break: clone");
  });

  it("screen과 print가 공통 스타일을 공유하고 출력 밀도만 분리한다", () => {
    const screenCss = createScopedContentCss(".document", "screen");
    const printCss = createScopedContentCss(".document", "print");

    expect(screenCss).toContain(".document table");
    expect(screenCss).not.toContain("font-size: 10pt");
    expect(screenCss).not.toContain("break-after: avoid-page");
    expect(printCss).toContain(".document table");
    expect(printCss).toContain("font-size: 10pt");
    expect(printCss).toContain("font-size: 8.5pt");
    expect(printCss).toContain("break-after: avoid-page");
  });
});

describe("createBrowserPrintCss", () => {
  it("다운로드 HTML을 인쇄할 때 A4 PDF 스타일을 적용한다", () => {
    const css = createBrowserPrintCss();

    expect(css).toContain("@media print");
    expect(css).toContain("size: A4 portrait");
    expect(css).toContain(".document-content h1");
    expect(css).toContain("font-size: 18pt !important");
    expect(css).toContain(".floating-section-nav");
    expect(css).toContain("display: none");
    expect(BASE_CSS).toContain(css);
  });
});

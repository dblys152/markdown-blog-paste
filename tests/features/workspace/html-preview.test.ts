import { describe, expect, it } from "vitest";

import { buildHtmlPreviewDocument } from "../../../src/features/workspace/html-preview";

describe("buildHtmlPreviewDocument", () => {
  it("완전한 HTML 문서를 body 안에 중첩하지 않고 CSP를 head에 삽입한다", () => {
    const result = buildHtmlPreviewDocument(`<!doctype html>
      <html lang="ko">
        <head><title>문서</title><style>body { color: red; }</style></head>
        <body><main>본문</main><script>window.alert('실행 금지')</script></body>
      </html>`);
    const document = new DOMParser().parseFromString(result, "text/html");

    expect(document.documentElement.lang).toBe("ko");
    expect(document.querySelectorAll("html")).toHaveLength(1);
    expect(document.querySelectorAll("body")).toHaveLength(1);
    expect(document.body.querySelector("main")?.textContent).toBe("본문");
    expect(document.head.firstElementChild?.getAttribute("http-equiv")).toBe("Content-Security-Policy");
    expect(document.head.firstElementChild?.getAttribute("content")).not.toContain("script-src");
    expect(document.head.firstElementChild?.getAttribute("content")).toContain("default-src 'none'");
  });

  it("HTML 조각을 미리보기 문서의 body로 구성한다", () => {
    const result = buildHtmlPreviewDocument("<section><h1>조각</h1></section>");
    const document = new DOMParser().parseFromString(result, "text/html");

    expect(document.body.innerHTML).toBe("<section><h1>조각</h1></section>");
    expect(document.head.querySelector('meta[http-equiv="Content-Security-Policy"]')).not.toBeNull();
  });
});

import { beforeEach, describe, expect, it, vi } from "vitest";

const { initializeMermaid, renderMermaid } = vi.hoisted(() => ({
  initializeMermaid: vi.fn(),
  renderMermaid: vi.fn(),
}));

vi.mock("mermaid", () => ({
  default: {
    initialize: initializeMermaid,
    render: renderMermaid,
  },
}));

import { renderMermaidDiagrams } from "../../../src/shared/markdown/mermaid-renderer";

describe("renderMermaidDiagrams", () => {
  beforeEach(() => {
    renderMermaid.mockReset();
  });

  it("Mermaid 코드블록을 접근 가능한 SVG figure로 교체한다", async () => {
    renderMermaid.mockResolvedValue({
      svg: '<svg viewBox="0 0 100 50"><text>diagram</text></svg>',
    });

    const html = await renderMermaidDiagrams(
      '<pre><code class="language-mermaid">graph TD\nA --&gt; B\n</code></pre>',
    );
    const template = document.createElement("template");
    template.innerHTML = html;

    expect(renderMermaid).toHaveBeenCalledOnce();
    expect(renderMermaid.mock.calls[0]?.[1]).toBe("graph TD\nA --> B");
    expect(template.content.querySelector("pre")).toBeNull();
    expect(template.content.querySelector("figure.mermaid-diagram svg")?.getAttribute("role")).toBe(
      "img",
    );
  });

  it("일반 코드블록은 변경하지 않는다", async () => {
    const source = '<pre><code class="language-ts">const value = 1;</code></pre>';

    expect(await renderMermaidDiagrams(source)).toBe(source);
    expect(renderMermaid).not.toHaveBeenCalled();
  });

  it("렌더링 실패 시 원본 코드와 오류 안내를 유지한다", async () => {
    renderMermaid.mockRejectedValue(new Error("invalid diagram"));

    const html = await renderMermaidDiagrams(
      '<pre><code class="language-mermaid">invalid</code></pre>',
    );
    const template = document.createElement("template");
    template.innerHTML = html;
    const codeBlock = template.content.querySelector("pre");

    expect(codeBlock?.textContent).toBe("invalid");
    expect(codeBlock?.classList.contains("mermaid-error")).toBe(true);
    expect(codeBlock?.getAttribute("title")).toBe("Mermaid 다이어그램을 렌더링할 수 없습니다.");
    expect(template.content.querySelector(".mermaid-diagram")).toBeNull();
  });
});

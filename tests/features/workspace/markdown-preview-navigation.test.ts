import { describe, expect, it, vi } from "vitest";
import { bindMarkdownPreviewNavigation } from "../../../src/features/workspace/markdown-preview-navigation";

describe("bindMarkdownPreviewNavigation", () => {
  it("네비게이션 클릭 시 문서를 이동하지 않고 대상 제목으로 스크롤한다", () => {
    document.body.innerHTML = `
      <a href="#section" data-section-target="section">섹션</a>
      <button data-section-target="section">바</button>
      <h2 id="section">섹션</h2>
    `;
    const heading = document.getElementById("section") as HTMLElement;
    heading.scrollIntoView = vi.fn();
    bindMarkdownPreviewNavigation(document);

    const link = document.querySelector("a") as HTMLAnchorElement;
    const event = new MouseEvent("click", { bubbles: true, cancelable: true });
    link.dispatchEvent(event);

    expect(event.defaultPrevented).toBe(true);
    expect(heading.scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth", block: "start" });
    expect(link.classList.contains("is-active")).toBe(true);
  });
});

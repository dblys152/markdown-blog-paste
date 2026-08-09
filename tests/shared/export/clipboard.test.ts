import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  copyPreviewHtml,
  preparePlainTextForClipboard,
  preparePreviewHtmlForClipboard,
} from "../../../src/shared/export/clipboard";

class ClipboardItemMock {
  constructor(readonly data: Record<string, Blob>) {}
}

describe("preparePreviewHtmlForClipboard", () => {
  it("Mermaid 영역을 순서가 표시된 자리 표시자로 교체한다", () => {
    const html = preparePreviewHtmlForClipboard(`
      <p>본문</p>
      <figure class="mermaid-diagram">
        <button class="mermaid-copy-button">복사</button>
        <svg><text>첫 번째</text></svg>
      </figure>
      <figure class="mermaid-diagram"><svg><text>두 번째</text></svg></figure>
    `);
    const template = document.createElement("template");
    template.innerHTML = html;
    const placeholders = template.content.querySelectorAll("[data-mermaid-placeholder]");

    expect(placeholders).toHaveLength(2);
    expect(placeholders[0]?.textContent).toContain("Mermaid 다이어그램 1 삽입 위치");
    expect(placeholders[1]?.textContent).toContain("Mermaid 다이어그램 2 삽입 위치");
    expect(template.content.querySelector(".mermaid-diagram")).toBeNull();
    expect(template.content.querySelector(".mermaid-copy-button")).toBeNull();
    expect(template.content.querySelector("svg")).toBeNull();
  });

  it("일반 본문과 이미지는 유지한다", () => {
    const html = preparePreviewHtmlForClipboard(
      '<p>본문</p><img src="https://example.com/image.png" alt="일반 이미지">',
    );
    const template = document.createElement("template");
    template.innerHTML = html;

    expect(template.content.querySelector("p")?.textContent).toBe("본문");
    expect(template.content.querySelector("img")?.getAttribute("src")).toBe(
      "https://example.com/image.png",
    );
  });
});

describe("copyPreviewHtml", () => {
  const clipboardWrite = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("ClipboardItem", ClipboardItemMock);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { write: clipboardWrite },
    });
    clipboardWrite.mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: undefined,
    });
  });

  it("HTML과 일반 텍스트를 Clipboard API에 함께 전달한다", async () => {
    const result = await copyPreviewHtml("<p>본문</p>");

    expect(result).toBe("html");
    expect(clipboardWrite).toHaveBeenCalledOnce();

    const items = clipboardWrite.mock.calls[0]?.[0] as ClipboardItemMock[];
    expect(items).toHaveLength(1);
    expect(Object.keys(items[0]?.data ?? {})).toEqual(["text/html", "text/plain"]);
    expect(items[0]?.data["text/html"]?.type).toBe("text/html");
    expect(items[0]?.data["text/plain"]?.type).toBe("text/plain");
  });

  it("목차 H2와 순서 목록을 HTML 및 일반 텍스트 클립보드에 유지한다", async () => {
    await copyPreviewHtml(
      '<h2 class="h2-toc-title">목차</h2><ol class="h2-toc-list"><li>제목 스타일</li><li>목록</li></ol><h2>1. 제목 스타일</h2>',
    );

    const items = clipboardWrite.mock.calls[0]?.[0] as ClipboardItemMock[];
    const html = preparePreviewHtmlForClipboard(
      '<h2 class="h2-toc-title">목차</h2><ol class="h2-toc-list"><li>제목 스타일</li><li>목록</li></ol><h2>1. 제목 스타일</h2>',
    );
    const plainText = preparePlainTextForClipboard(html);

    expect(html).toContain('<h2 class="h2-toc-title">목차</h2>');
    expect(html).toContain('<ol class="h2-toc-list"><li>제목 스타일</li><li>목록</li></ol>');
    expect(plainText).toContain("목차\n\n1. 제목 스타일\n2. 목록");
    expect(plainText).toContain("1. 제목 스타일");
  });

  it("Clipboard API가 없으면 execCommand fallback을 사용한다", async () => {
    vi.stubGlobal("ClipboardItem", undefined);
    const execCommand = vi.fn().mockReturnValue(true);
    Object.defineProperty(document, "execCommand", {
      configurable: true,
      value: execCommand,
    });

    expect(await copyPreviewHtml("<p>본문</p>")).toBe("html");
    expect(execCommand).toHaveBeenCalledWith("copy");
    expect(document.querySelector('[contenteditable="true"]')).toBeNull();
  });

  it("Clipboard API 쓰기가 실패하면 execCommand fallback으로 재시도한다", async () => {
    clipboardWrite.mockRejectedValue(new Error("permission denied"));
    const execCommand = vi.fn().mockReturnValue(true);
    Object.defineProperty(document, "execCommand", {
      configurable: true,
      value: execCommand,
    });

    expect(await copyPreviewHtml("<p>본문</p>")).toBe("html");
    expect(execCommand).toHaveBeenCalledWith("copy");
  });

  it("모든 HTML 복사 방식이 실패하면 text 결과를 반환한다", async () => {
    vi.stubGlobal("ClipboardItem", undefined);
    Object.defineProperty(document, "execCommand", {
      configurable: true,
      value: vi.fn().mockReturnValue(false),
    });

    expect(await copyPreviewHtml("<p>본문</p>")).toBe("text");
  });
});

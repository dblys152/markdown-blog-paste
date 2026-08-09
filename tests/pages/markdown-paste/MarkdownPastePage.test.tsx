import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { convertMarkdown, copyPreviewHtml, downloadHtml, downloadPdf } = vi.hoisted(() => ({
  convertMarkdown: vi.fn(),
  copyPreviewHtml: vi.fn(),
  downloadHtml: vi.fn(),
  downloadPdf: vi.fn(),
}));

vi.mock("../../../src/shared/markdown/converter-core", () => ({ convertMarkdown }));
vi.mock("../../../src/shared/export/clipboard", () => ({
  copyMermaidPng: vi.fn(),
  copyPreviewHtml,
}));
vi.mock("../../../src/shared/export/html-export", () => ({ downloadHtml }));
vi.mock("../../../src/shared/export/pdf-export", () => ({ downloadPdf }));

import { MarkdownPastePage } from "../../../src/pages/markdown-paste/MarkdownPastePage";

const conversionResult = {
  bodyHtml: "<p>변환된 본문</p>",
  fullHtml:
    '<!doctype html><html><head><style>.document-layout { max-width: 800px; }</style></head><body><p>변환된 본문</p></body></html>',
};

describe("MarkdownPastePage", () => {
  beforeEach(() => {
    convertMarkdown.mockResolvedValue(conversionResult);
    copyPreviewHtml.mockResolvedValue("html");
    downloadPdf.mockResolvedValue(undefined);
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("샘플 Markdown을 변환해 미리보기를 표시한다", async () => {
    render(<MarkdownPastePage />);

    const preview = await screen.findByTitle<HTMLIFrameElement>("변환 결과");

    expect(convertMarkdown).toHaveBeenCalledWith(expect.stringContaining("# "), "basic", "sample-post");
    expect(preview.srcdoc).toContain("변환된 본문");
    expect(screen.getByText("sample-post.md")).not.toBeNull();
  });

  it("변환 모드를 변경하면 Markdown을 다시 변환한다", async () => {
    const user = userEvent.setup();
    render(<MarkdownPastePage />);
    await screen.findByTitle("변환 결과");

    await user.click(screen.getByRole("radio", { name: /네이버 블로그용/ }));

    await waitFor(() => {
      expect(convertMarkdown).toHaveBeenLastCalledWith(
        expect.stringContaining("# "),
        "naver",
        "sample-post",
      );
    });
  });

  it("미리보기 스타일을 변경하면 iframe 문서를 갱신한다", async () => {
    const user = userEvent.setup();
    render(<MarkdownPastePage />);
    const preview = await screen.findByTitle<HTMLIFrameElement>("변환 결과");

    await user.selectOptions(screen.getByLabelText("미리보기 스타일"), "compact");

    expect(preview.srcdoc).toContain("max-width: 660px");
  });

  it("미리보기 복사 결과를 토스트로 안내한다", async () => {
    const user = userEvent.setup();
    render(<MarkdownPastePage />);
    await screen.findByTitle("변환 결과");

    await user.click(screen.getByRole("button", { name: "미리보기 내용 복사" }));

    expect(copyPreviewHtml).toHaveBeenCalledWith("<p>변환된 본문</p>");
    expect(screen.getByText("미리보기 HTML을 클립보드에 복사했습니다.")).not.toBeNull();
  });
});

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { convertMarkdown, copyPreviewHtml, downloadHtml, downloadPdf, loadGuestDraft, saveGuestDraft } = vi.hoisted(() => ({
  convertMarkdown: vi.fn(),
  copyPreviewHtml: vi.fn(),
  downloadHtml: vi.fn(),
  downloadPdf: vi.fn(),
  loadGuestDraft: vi.fn(),
  saveGuestDraft: vi.fn(),
}));

vi.mock("../../../src/shared/markdown/converter-core", () => ({ convertMarkdown }));
vi.mock("../../../src/shared/export/clipboard", () => ({
  copyMermaidPng: vi.fn(),
  copyPreviewHtml,
}));
vi.mock("../../../src/shared/export/html-export", () => ({ downloadHtml }));
vi.mock("../../../src/shared/export/pdf-export", () => ({ downloadPdf }));
vi.mock("../../../src/pages/workspace/guest-draft-store", () => ({ loadGuestDraft, saveGuestDraft }));

import { MarkdownPastePage } from "../../../src/pages/markdown-paste/MarkdownPastePage";

function renderPage() {
  return render(
    <MemoryRouter>
      <MarkdownPastePage />
    </MemoryRouter>,
  );
}

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
    loadGuestDraft.mockResolvedValue(null);
    saveGuestDraft.mockResolvedValue(undefined);
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("샘플 Markdown을 변환해 미리보기를 표시한다", async () => {
    renderPage();

    const preview = await screen.findByTitle<HTMLIFrameElement>("변환 결과");

    expect(convertMarkdown).toHaveBeenCalledWith(expect.stringContaining("# "), "basic", "sample-post", {
      excludeFirstH1: false,
      generateH2Toc: false,
      addH2Dividers: false,
    }, expect.any(Function));
    expect(preview.srcdoc).toContain("변환된 본문");
    expect(screen.getByText("sample-post.md")).not.toBeNull();
  });

  it("변환 모드를 변경하면 Markdown을 다시 변환한다", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByTitle("변환 결과");

    await user.click(screen.getByRole("radio", { name: /네이버 블로그/ }));

    await waitFor(() => {
      expect(convertMarkdown).toHaveBeenLastCalledWith(
        expect.stringContaining("# "),
        "naver",
        "sample-post",
        { excludeFirstH1: false, generateH2Toc: false, addH2Dividers: false },
        expect.any(Function),
      );
    });
  });

  it("추가 옵션을 변경하면 즉시 다시 변환한다", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByTitle("변환 결과");

    await user.click(screen.getByRole("checkbox", { name: "H2 목차 자동 생성" }));

    await waitFor(() => {
      expect(convertMarkdown).toHaveBeenLastCalledWith(expect.stringContaining("# "), "basic", "sample-post", {
        excludeFirstH1: false,
        generateH2Toc: true,
        addH2Dividers: false,
      }, expect.any(Function));
    });
  });

  it("내보내기 메뉴에서 HTML을 다운로드한다", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByTitle("변환 결과");

    await user.click(screen.getByRole("button", { name: /내보내기/ }));
    await user.click(screen.getByRole("menuitem", { name: /HTML 다운로드/ }));

    expect(downloadHtml).toHaveBeenCalledWith(conversionResult.fullHtml, "sample-post");
  });

  it("미리보기 복사 결과를 토스트로 안내한다", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByTitle("변환 결과");

    await user.click(screen.getByRole("button", { name: "미리보기 내용 복사" }));

    expect(copyPreviewHtml).toHaveBeenCalledWith("<p>변환된 본문</p>");
    expect(screen.getByText("미리보기 HTML을 클립보드에 복사했습니다.")).not.toBeNull();
  });

  it("원본 Markdown 탭에서 업로드된 원문을 표시한다", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByTitle("변환 결과");

    await user.click(screen.getByRole("tab", { name: "원본 Markdown" }));

    expect(screen.getByText((content) => content.includes("Markdown Blog Post 예시"))).not.toBeNull();
    expect(screen.queryByTitle("변환 결과")).toBeNull();
  });

  it("기록장에 저장 버튼은 즉시 저장하지 않고 교체가 기본인 선택 창을 연다", async () => {
    const user = userEvent.setup();
    loadGuestDraft.mockResolvedValue({ title: "기존 페이지", markdown: "기존 내용", updatedAt: 1 });
    renderPage();
    await screen.findByTitle("변환 결과");

    await user.click(screen.getByRole("button", { name: "기록장에 저장" }));

    expect(saveGuestDraft).not.toHaveBeenCalled();
    expect(await screen.findByRole("dialog", { name: "기록장에 저장" })).not.toBeNull();
    expect((screen.getByRole("radio", { name: "임시 페이지를 현재 내용으로 교체" }) as HTMLInputElement).checked).toBe(true);
    expect(screen.getByText("기존 임시 페이지 내용이 현재 내용으로 교체됩니다.")).not.toBeNull();
  });

  it("내용 추가를 선택하면 기존 본문 뒤에 현재 Markdown을 이어 저장한다", async () => {
    const user = userEvent.setup();
    loadGuestDraft.mockResolvedValue({ title: "기존 페이지", markdown: "기존 내용\n", updatedAt: 1 });
    renderPage();
    await screen.findByTitle("변환 결과");

    await user.click(screen.getByRole("button", { name: "기록장에 저장" }));
    await user.click(await screen.findByRole("radio", { name: "임시 페이지에 내용 추가" }));
    await user.click(screen.getByRole("button", { name: "임시 페이지에 저장" }));

    await waitFor(() => {
      expect(saveGuestDraft).toHaveBeenCalledWith({
        title: "임시 페이지",
        markdown: expect.stringMatching(/^기존 내용\n\n# /),
        updatedAt: expect.any(Number),
      });
    });
  });

  it("교체 저장에서도 비회원 페이지 이름은 임시 페이지로 유지한다", async () => {
    const user = userEvent.setup();
    loadGuestDraft.mockResolvedValue({ title: "잘못 저장된 파일명", markdown: "기존 내용", updatedAt: 1 });
    renderPage();
    await screen.findByTitle("변환 결과");

    await user.click(screen.getByRole("button", { name: "기록장에 저장" }));
    await user.click(await screen.findByRole("button", { name: "임시 페이지에 저장" }));

    await waitFor(() => {
      expect(saveGuestDraft).toHaveBeenCalledWith({
        title: "임시 페이지",
        markdown: expect.stringMatching(/^# /),
        updatedAt: expect.any(Number),
      });
    });
  });
});

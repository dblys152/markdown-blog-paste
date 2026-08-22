import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const {
  convertMarkdown,
  copyPreviewHtml,
  downloadHtml,
  downloadPdf,
  loadGuestDraft,
  saveGuestDraft,
  useAuth,
  listWorkspacePages,
  getWorkspacePage,
  createWorkspacePage,
  updateWorkspacePage,
} = vi.hoisted(() => ({
  convertMarkdown: vi.fn(),
  copyPreviewHtml: vi.fn(),
  downloadHtml: vi.fn(),
  downloadPdf: vi.fn(),
  loadGuestDraft: vi.fn(),
  saveGuestDraft: vi.fn(),
  useAuth: vi.fn(),
  listWorkspacePages: vi.fn(),
  getWorkspacePage: vi.fn(),
  createWorkspacePage: vi.fn(),
  updateWorkspacePage: vi.fn(),
}));

vi.mock("../../../src/shared/markdown/converter-core", () => ({ convertMarkdown }));
vi.mock("../../../src/shared/export/clipboard", () => ({
  copyMermaidPng: vi.fn(),
  copyPreviewHtml,
}));
vi.mock("../../../src/shared/export/html-export", () => ({ downloadHtml }));
vi.mock("../../../src/shared/export/pdf-export", () => ({ downloadPdf }));
vi.mock("../../../src/pages/workspace/guest-draft-store", () => ({ loadGuestDraft, saveGuestDraft }));
vi.mock("../../../src/features/auth/AuthProvider", () => ({ useAuth }));
vi.mock("../../../src/features/workspace/api", () => ({
  listWorkspacePages,
  getWorkspacePage,
  createWorkspacePage,
  updateWorkspacePage,
}));

import { MarkdownPastePage } from "../../../src/pages/markdown-paste/MarkdownPastePage";
import { clearQuickConversionDraft } from "../../../src/pages/markdown-paste/quick-conversion-draft-store";

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
    clearQuickConversionDraft();
    convertMarkdown.mockResolvedValue(conversionResult);
    copyPreviewHtml.mockResolvedValue("html");
    downloadPdf.mockResolvedValue(undefined);
    loadGuestDraft.mockResolvedValue(null);
    saveGuestDraft.mockResolvedValue(undefined);
    useAuth.mockReturnValue({ status: "guest", user: null });
    listWorkspacePages.mockResolvedValue([]);
    getWorkspacePage.mockResolvedValue({
      id: "10",
      title: "개발 노트",
      content: "기존 내용",
      parent_id: null,
      sort_order: 0,
    });
    createWorkspacePage.mockResolvedValue(undefined);
    updateWorkspacePage.mockResolvedValue(undefined);
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("샘플 Markdown을 변환해 미리보기를 표시한다", async () => {
    renderPage();

    const preview = await screen.findByTitle<HTMLIFrameElement>("변환 결과");

    expect(screen.getByRole("tab", { name: "변환 설정" }).getAttribute("aria-selected")).toBe("true");
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

  it("다른 화면을 다녀와도 업로드한 Markdown 작업을 복원한다", async () => {
    const user = userEvent.setup();
    const firstRender = renderPage();
    const file = new File(["# 유지되는 문서"], "kept.md", { type: "text/markdown" });
    Object.defineProperty(file, "text", { value: vi.fn().mockResolvedValue("# 유지되는 문서") });

    await user.upload(screen.getByLabelText("Markdown 파일 선택"), file);
    await screen.findByText("kept.md");
    await waitFor(() => {
      expect(screen.getByRole("tablist", { name: "빠른 변환 화면" }).querySelector('[aria-selected="true"]')?.textContent).toBe("미리보기");
    });
    firstRender.unmount();

    renderPage();

    expect(await screen.findByText("kept.md")).not.toBeNull();
    expect(screen.getByRole("tab", { name: "원본 Markdown" })).not.toBeNull();
    expect(convertMarkdown).toHaveBeenLastCalledWith(
      "# 유지되는 문서",
      "basic",
      "kept",
      { excludeFirstH1: false, generateH2Toc: false, addH2Dividers: false },
      expect.any(Function),
    );
  });

  it("파일을 연속으로 불러오면 두 번째 문서 변환 후 미리보기를 표시한다", async () => {
    const user = userEvent.setup();
    convertMarkdown.mockImplementation(async (markdown: string) => ({
      bodyHtml: `<p>${markdown}</p>`,
      fullHtml: `<!doctype html><html><body><p>${markdown}</p></body></html>`,
    }));
    renderPage();
    const firstFile = new File(["# 첫 번째"], "first.md", { type: "text/markdown" });
    const secondFile = new File(["# 두 번째"], "second.md", { type: "text/markdown" });
    Object.defineProperty(firstFile, "text", { value: vi.fn().mockResolvedValue("# 첫 번째") });
    Object.defineProperty(secondFile, "text", { value: vi.fn().mockResolvedValue("# 두 번째") });

    await user.upload(screen.getByLabelText("Markdown 파일 선택"), firstFile);
    await screen.findByText("first.md");
    await user.click(screen.getByRole("tab", { name: "변환 설정" }));
    await user.upload(screen.getByLabelText("Markdown 파일 선택"), secondFile);

    await waitFor(() => {
      expect(convertMarkdown).toHaveBeenLastCalledWith(
        "# 두 번째",
        "basic",
        "second",
        { excludeFirstH1: false, generateH2Toc: false, addH2Dividers: false },
        expect.any(Function),
      );
      expect(screen.getByRole("tablist", { name: "빠른 변환 화면" }).querySelector('[aria-selected="true"]')?.textContent).toBe("미리보기");
      expect(screen.getByTitle<HTMLIFrameElement>("변환 결과").srcdoc).toContain("# 두 번째");
    });
  });

  it("전체 초기화는 파일과 변환 옵션을 기본값으로 되돌린다", async () => {
    const user = userEvent.setup();
    renderPage();
    const file = new File(["# 초기화 대상"], "reset-target.md", { type: "text/markdown" });
    Object.defineProperty(file, "text", { value: vi.fn().mockResolvedValue("# 초기화 대상") });

    await user.upload(screen.getByLabelText("Markdown 파일 선택"), file);
    await user.click(screen.getByRole("radio", { name: /네이버 블로그/ }));
    await user.click(screen.getByRole("checkbox", { name: "H2 목차 자동 생성" }));
    await user.click(screen.getByRole("button", { name: "전체 초기화" }));

    expect(screen.getByText("sample-post.md")).not.toBeNull();
    expect((screen.getByRole("radio", { name: /표준 변환/ }) as HTMLInputElement).checked).toBe(true);
    expect((screen.getByRole("checkbox", { name: "H2 목차 자동 생성" }) as HTMLInputElement).checked).toBe(false);
    expect(screen.getByText("빠른 변환 작업을 초기화했습니다.")).not.toBeNull();
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

  it("로그인 사용자는 임시 페이지 대신 서버 기록장 저장 대상을 선택한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1" } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "개발 노트", parent_id: null, sort_order: 0 },
    ]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByTitle("변환 결과");

    await user.click(screen.getByRole("button", { name: "기록장에 저장" }));

    const dialog = await screen.findByRole("dialog", { name: "기록장에 저장" });
    expect(within(dialog).queryByText("임시 페이지를 현재 내용으로 교체")).toBeNull();
    expect(within(dialog).getByRole("option", { name: "새 페이지로 저장" })).not.toBeNull();
    expect(within(dialog).getByRole("option", { name: "개발 노트" })).not.toBeNull();

    await user.click(within(dialog).getByRole("button", { name: "기록장에 저장" }));

    await waitFor(() => {
      expect(createWorkspacePage).toHaveBeenCalledWith({
        title: "sample-post",
        content: expect.stringContaining("# "),
        parent_id: null,
      });
    });
    expect(saveGuestDraft).not.toHaveBeenCalled();
  });
});

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const {
  convertMarkdown,
  loadGuestDraft,
  saveGuestDraft,
  useAuth,
  listWorkspacePages,
  getWorkspacePage,
  getTrashedWorkspacePage,
  createWorkspacePage,
  createPdfWorkspacePage,
  getWorkspacePdfBlob,
  getWorkspacePdfUrl,
  updateWorkspacePage,
  deleteWorkspacePage,
  moveWorkspacePage,
  listTrashedWorkspacePages,
  restoreWorkspacePage,
  searchWorkspacePages,
  permanentlyDeleteWorkspacePage,
} = vi.hoisted(() => ({
  convertMarkdown: vi.fn(),
  loadGuestDraft: vi.fn(),
  saveGuestDraft: vi.fn(),
  useAuth: vi.fn(),
  listWorkspacePages: vi.fn(),
  getWorkspacePage: vi.fn(),
  getTrashedWorkspacePage: vi.fn(),
  createWorkspacePage: vi.fn(),
  createPdfWorkspacePage: vi.fn(),
  getWorkspacePdfBlob: vi.fn(),
  getWorkspacePdfUrl: vi.fn(),
  updateWorkspacePage: vi.fn(),
  deleteWorkspacePage: vi.fn(),
  moveWorkspacePage: vi.fn(),
  listTrashedWorkspacePages: vi.fn(),
  restoreWorkspacePage: vi.fn(),
  searchWorkspacePages: vi.fn(),
  permanentlyDeleteWorkspacePage: vi.fn(),
}));

vi.mock("../../../src/shared/markdown/converter-core", () => ({ convertMarkdown }));
vi.mock("../../../src/pages/workspace/guest-draft-store", () => ({ loadGuestDraft, saveGuestDraft }));
vi.mock("../../../src/features/auth/AuthProvider", () => ({ useAuth }));
vi.mock("../../../src/features/workspace/api", () => ({
  listWorkspacePages,
  getWorkspacePage,
  getTrashedWorkspacePage,
  createWorkspacePage,
  createPdfWorkspacePage,
  getWorkspacePdfBlob,
  getWorkspacePdfUrl,
  updateWorkspacePage,
  deleteWorkspacePage,
  moveWorkspacePage,
  listTrashedWorkspacePages,
  restoreWorkspacePage,
  searchWorkspacePages,
  permanentlyDeleteWorkspacePage,
}));

import { WorkspaceGatePage } from "../../../src/pages/workspace/WorkspaceGatePage";

const storageValues = new Map<string, string>();
Object.defineProperty(window, "localStorage", {
  configurable: true,
  value: {
    clear: () => storageValues.clear(),
    getItem: (key: string) => storageValues.get(key) ?? null,
    removeItem: (key: string) => storageValues.delete(key),
    setItem: (key: string, value: string) => storageValues.set(key, String(value)),
  },
});

const conversionResult = {
  bodyHtml: "<p>미리보기</p>",
  fullHtml: "<!doctype html><html><body><p>미리보기</p></body></html>",
};

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function renderPage(initialEntry: string | { pathname: string; state?: unknown } = "/workspace") {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <WorkspaceGatePage />
    </MemoryRouter>,
  );
}

describe("WorkspaceGatePage", () => {
  beforeEach(() => {
    window.localStorage.clear();
    loadGuestDraft.mockResolvedValue(null);
    saveGuestDraft.mockResolvedValue(undefined);
    convertMarkdown.mockResolvedValue(conversionResult);
    useAuth.mockReturnValue({ status: "guest", user: null });
    listWorkspacePages.mockResolvedValue([]);
    getWorkspacePage.mockImplementation(async (pageId: string) => ({
      id: pageId,
      title: "페이지",
      contents: "",
      parent_id: null,
      sort_order: 0,
    }));
    getTrashedWorkspacePage.mockImplementation(async (pageId: string) => ({
      id: pageId,
      owner_id: "1",
      title: "삭제한 페이지",
      contents: "# 삭제한 페이지",
      parent_id: null,
      sort_order: 0,
    }));
    createWorkspacePage.mockResolvedValue({
      id: "10",
      title: "새 페이지",
      contents: "# 새 페이지\n",
      parent_id: null,
      sort_order: 0,
    });
    createPdfWorkspacePage.mockResolvedValue({
      id: "30",
      title: "문서",
      type: "PDF",
      contents: null,
      file_name: "document.pdf",
      file_size: 8,
      parent_id: null,
      sort_order: 0,
    });
    getWorkspacePdfBlob.mockResolvedValue(new Blob(["%PDF-1.7"], { type: "application/pdf" }));
    getWorkspacePdfUrl.mockResolvedValue({ url: "https://example.test/document.pdf", expires_in: "900" });
    updateWorkspacePage.mockImplementation(async (id, input) => ({
      id,
      title: input.title ?? "페이지",
      contents: input.content ?? "",
      parent_id: null,
      sort_order: 0,
    }));
    deleteWorkspacePage.mockResolvedValue(undefined);
    moveWorkspacePage.mockImplementation(async (id, input) => ({
      id,
      title: "이동한 페이지",
      contents: "",
      parent_id: input.parent_id,
      sort_order: input.sort_order,
    }));
    listTrashedWorkspacePages.mockResolvedValue([]);
    restoreWorkspacePage.mockResolvedValue(undefined);
    searchWorkspacePages.mockResolvedValue([]);
    permanentlyDeleteWorkspacePage.mockResolvedValue(undefined);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.clearAllMocks();
    vi.unstubAllGlobals();
  });

  it("로그인 상태 확인 중에는 임시 페이지를 표시하지 않는다", () => {
    useAuth.mockReturnValue({ status: "loading", user: null });

    renderPage();

    expect(screen.getByText("내 기록장을 불러오는 중…")).not.toBeNull();
    expect(screen.queryByText("임시 페이지")).toBeNull();
    expect(loadGuestDraft).not.toHaveBeenCalled();
  });

  it("회원 페이지 API 응답 전에도 임시 페이지를 표시하지 않는다", () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockReturnValue(new Promise(() => undefined));

    renderPage();

    expect(screen.getByText("내 기록장을 불러오는 중…")).not.toBeNull();
    expect(screen.queryByText("임시 페이지")).toBeNull();
    expect(loadGuestDraft).not.toHaveBeenCalled();
  });

  it("기록장 저장 후 전달된 페이지를 첫 화면에서 선택한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "첫 페이지", parent_id: null, sort_order: 0 },
      { id: "20", owner_id: "1", title: "저장한 페이지", parent_id: null, sort_order: 1 },
    ]);

    renderPage({ pathname: "/workspace", state: { selectedPageId: "20" } });

    await waitFor(() => expect(getWorkspacePage).toHaveBeenCalledWith("20"));
    expect(screen.getByRole("button", { name: "저장한 페이지" }).closest(".workspace-page-item")?.classList.contains("is-active")).toBe(true);
    expect(getWorkspacePage).not.toHaveBeenCalledWith("10");
  });

  it("페이지를 기본으로 접고 아이콘에서 하위 페이지를 펼치거나 다시 접는다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "개발 노트", parent_id: null, sort_order: 0 },
      { id: "20", owner_id: "1", title: "API 설계", parent_id: "10", sort_order: 0 },
    ]);
    const user = userEvent.setup();

    renderPage();

    const expandButton = await screen.findByRole("button", { name: "개발 노트 하위 페이지 펼치기" });
    expect(screen.getByRole("button", { name: "개발 노트" }).querySelector(".workspace-page-child-count")?.textContent).toBe("1");
    expect(screen.getByRole("button", { name: "개발 노트" }).getAttribute("aria-label")).toBeNull();
    expect(screen.queryByRole("button", { name: "API 설계" })).toBeNull();

    await user.click(expandButton);
    expect(screen.getByRole("button", { name: "API 설계" })).not.toBeNull();
    expect(screen.queryByRole("button", { name: "API 설계 하위 페이지 펼치기" })).toBeNull();
    expect(screen.getByRole("button", { name: "API 설계" }).closest(".workspace-page-item")?.querySelector(".workspace-page-icon")).not.toBeNull();

    await user.click(screen.getByRole("button", { name: "개발 노트 하위 페이지 접기" }));
    expect(screen.queryByRole("button", { name: "API 설계" })).toBeNull();
  });

  it("페이지 펼침 상태를 사용자별로 저장하고 다시 진입할 때 복원한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "user-1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "user-1", title: "개발 노트", parent_id: null, sort_order: 0 },
      { id: "20", owner_id: "user-1", title: "API 설계", parent_id: "10", sort_order: 0 },
    ]);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "개발 노트 하위 페이지 펼치기" }));
    expect(screen.getByRole("button", { name: "API 설계" })).not.toBeNull();

    cleanup();
    renderPage();
    expect(await screen.findByRole("button", { name: "API 설계" })).not.toBeNull();

    cleanup();
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "user-2", email_verified: true } });
    renderPage();
    await screen.findByRole("button", { name: "개발 노트 하위 페이지 펼치기" });
    expect(screen.queryByRole("button", { name: "API 설계" })).toBeNull();
  });

  it("페이지 탭에서 임시 페이지를 선택하면 Markdown 탭으로 이동한다", async () => {
    const user = userEvent.setup();
    renderPage();

    expect(screen.getByRole("button", { name: "임시 페이지" }).querySelector(".workspace-page-type-icon.is-markdown")).not.toBeNull();
    expect((screen.getByRole("textbox", { name: "Markdown 내용" }) as HTMLTextAreaElement).value)
      .toContain("# 임시 Markdown 페이지");
    expect(screen.getByRole("tab", { name: "페이지" }).getAttribute("aria-selected")).toBe("true");
    await user.click(screen.getByRole("button", { name: "임시 페이지" }));

    expect(screen.getByRole("tab", { name: "Markdown" }).getAttribute("aria-selected")).toBe("true");
  });

  it("페이지 유형별 아이콘을 표시하고 HTML 페이지는 격리된 미리보기와 외부 이미지 안내를 제공한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "Markdown 문서", parent_id: null, sort_order: 0, type: "MARKDOWN" },
      { id: "20", owner_id: "1", title: "HTML 문서", parent_id: null, sort_order: 1, type: "HTML" },
      { id: "25", owner_id: "1", title: "회의 메모", parent_id: null, sort_order: 2, type: "MEMO" },
      { id: "30", owner_id: "1", title: "PDF 문서", parent_id: null, sort_order: 3, type: "PDF" },
    ]);
    getWorkspacePage.mockImplementation(async (pageId: string) => ({
      id: pageId,
      title: pageId === "20" ? "HTML 문서" : "Markdown 문서",
      type: pageId === "20" ? "HTML" : "MARKDOWN",
      contents: pageId === "20" ? '<img src="https://example.com/photo.jpg">' : "# Markdown",
      parent_id: null,
      sort_order: pageId === "20" ? 1 : 0,
    }));
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByRole("img", { name: "Markdown 문서" })).not.toBeNull();
    expect(screen.getByRole("img", { name: "HTML 문서" })).not.toBeNull();
    expect(screen.getByRole("img", { name: "메모 문서" })).not.toBeNull();
    expect(screen.getByRole("img", { name: "PDF 문서" })).not.toBeNull();

    await user.click(screen.getByRole("button", { name: "HTML 문서" }));

    expect(await screen.findByRole("region", { name: "HTML 편집기" })).not.toBeNull();
    expect(screen.getByText("외부 이미지를 불러오면 이미지 서버에 현재 사용자의 IP가 전달될 수 있습니다.")).not.toBeNull();
    const preview = screen.getByTitle<HTMLIFrameElement>("HTML 문서 미리보기");
    expect(preview.getAttribute("sandbox")).toBe("");
    expect(preview.getAttribute("referrerpolicy")).toBe("no-referrer");
    await waitFor(() => expect(preview.srcdoc).toContain("https://example.com/photo.jpg"));
  });

  it("메모 페이지는 Markdown 변환과 미리보기 없이 전체 너비 편집기로 표시한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "Markdown 문서", parent_id: null, sort_order: 0, type: "MARKDOWN" },
      { id: "20", owner_id: "1", title: "회의 메모", parent_id: null, sort_order: 1, type: "MEMO" },
    ]);
    getWorkspacePage.mockImplementation(async (pageId: string) => ({
      id: pageId,
      owner_id: "1",
      title: pageId === "20" ? "회의 메모" : "Markdown 문서",
      type: pageId === "20" ? "MEMO" : "MARKDOWN",
      contents: pageId === "20" ? "안건 확인\n담당자 지정" : "# Markdown",
      parent_id: null,
      sort_order: pageId === "20" ? 1 : 0,
    }));
    const user = userEvent.setup();
    renderPage();

    await screen.findByDisplayValue("# Markdown");
    convertMarkdown.mockClear();
    await user.click(screen.getByRole("button", { name: "회의 메모" }));

    const editor = await screen.findByRole("region", { name: "메모 편집기" });
    expect(editor.classList.contains("is-memo-editor")).toBe(true);
    expect(screen.getByRole("textbox", { name: "메모 내용" })).toHaveProperty("value", "안건 확인\n담당자 지정");
    expect(screen.queryByRole("region", { name: "미리보기" })).toBeNull();
    expect(screen.queryByRole("separator", { name: "에디터와 미리보기 너비 조절" })).toBeNull();
    expect(screen.queryByRole("tab", { name: "미리보기" })).toBeNull();
    expect(screen.getByRole("tab", { name: "메모" }).getAttribute("aria-selected")).toBe("true");
    expect(convertMarkdown.mock.calls.some(([content]) => content === "안건 확인\n담당자 지정")).toBe(false);
  });

  it("HTML 페이지에서는 Markdown 변환을 실행하지 않는다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "Markdown 문서", parent_id: null, sort_order: 0, type: "MARKDOWN" },
      { id: "20", owner_id: "1", title: "HTML 문서", parent_id: null, sort_order: 1, type: "HTML" },
    ]);
    getWorkspacePage.mockImplementation(async (pageId: string) => ({
      id: pageId,
      title: pageId === "20" ? "HTML 문서" : "Markdown 문서",
      type: pageId === "20" ? "HTML" : "MARKDOWN",
      contents: pageId === "20" ? "<h1>HTML</h1>" : "# Markdown",
      parent_id: null,
      sort_order: pageId === "20" ? 1 : 0,
    }));
    const user = userEvent.setup();
    renderPage();

    await screen.findByDisplayValue("# Markdown");
    await waitFor(() => expect(convertMarkdown).toHaveBeenCalled());
    convertMarkdown.mockClear();
    await user.click(screen.getByRole("button", { name: "HTML 문서" }));
    await screen.findByTitle("HTML 문서 미리보기");

    expect(convertMarkdown).not.toHaveBeenCalled();
  });

  it("페이지 행에 마우스를 올리면 상세를 선로딩하고 선택 시 같은 요청을 재사용한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "첫 페이지", parent_id: null, sort_order: 0, type: "MARKDOWN" },
      { id: "20", owner_id: "1", title: "둘째 페이지", parent_id: null, sort_order: 1, type: "MARKDOWN" },
    ]);
    const secondPage = createDeferred<{
      id: string;
      title: string;
      type: "MARKDOWN";
      contents: string;
      parent_id: null;
      sort_order: number;
    }>();
    getWorkspacePage.mockImplementation((pageId: string) => pageId === "20"
      ? secondPage.promise
      : Promise.resolve({
        id: "10",
        title: "첫 페이지",
        type: "MARKDOWN",
        contents: "첫 내용",
        parent_id: null,
        sort_order: 0,
      }));
    const user = userEvent.setup();
    renderPage();

    await screen.findByDisplayValue("첫 내용");
    const secondPageRow = screen.getByRole("button", { name: "둘째 페이지" }).closest(".workspace-page-item") as HTMLElement;
    fireEvent.mouseEnter(secondPageRow);
    await waitFor(() => expect(getWorkspacePage).toHaveBeenCalledWith("20"));
    const clickPromise = user.click(secondPageRow);
    await waitFor(() => expect(secondPageRow.classList.contains("is-active")).toBe(true));
    expect(getWorkspacePage.mock.calls.filter(([pageId]) => pageId === "20")).toHaveLength(1);
    secondPage.resolve({
      id: "20",
      title: "둘째 페이지",
      type: "MARKDOWN",
      contents: "둘째 내용",
      parent_id: null,
      sort_order: 1,
    });
    await clickPromise;
    await screen.findByDisplayValue("둘째 내용");
    expect(getWorkspacePage.mock.calls.filter(([pageId]) => pageId === "20")).toHaveLength(1);
  });

  it("저장된 PDF Blob을 재선택 시 재사용하고 기록장을 벗어날 때 해제한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "30", owner_id: "1", title: "PDF 원본", parent_id: null, sort_order: 0, type: "PDF" },
      { id: "10", owner_id: "1", title: "Markdown 문서", parent_id: null, sort_order: 1, type: "MARKDOWN" },
    ]);
    getWorkspacePage.mockImplementation(async (pageId: string) => ({
      id: pageId,
      title: pageId === "30" ? "PDF 원본" : "Markdown 문서",
      type: pageId === "30" ? "PDF" : "MARKDOWN",
      contents: pageId === "30" ? null : "# Markdown",
      parent_id: null,
      sort_order: pageId === "30" ? 0 : 1,
    }));
    getWorkspacePdfUrl.mockResolvedValue({ url: "/workspace/pages/30/pdf/content", expires_in: "900" });
    const pdfBlob = new Blob(["%PDF-1.7\nPDF contents"], { type: "application/pdf" });
    getWorkspacePdfBlob.mockResolvedValue(pdfBlob);
    const createObjectURL = vi.fn(() => "blob:https://md2blog.test/pdf-original");
    const revokeObjectURL = vi.fn();
    class MockURL extends URL {}
    MockURL.createObjectURL = createObjectURL;
    MockURL.revokeObjectURL = revokeObjectURL;
    vi.stubGlobal("URL", MockURL);
    const user = userEvent.setup();
    const view = renderPage();

    const pdfPreview = await screen.findByTitle<HTMLIFrameElement>("PDF 원본 PDF");
    expect(getWorkspacePdfBlob).toHaveBeenCalledWith("/workspace/pages/30/pdf/content");
    expect(createObjectURL).toHaveBeenCalledWith(pdfBlob);
    expect(pdfPreview.src).toBe("blob:https://md2blog.test/pdf-original");

    await user.click(screen.getByRole("button", { name: "Markdown 문서" }));
    expect(screen.queryByTitle("PDF 원본 PDF")).toBeNull();
    expect(revokeObjectURL).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "PDF 원본" }));
    expect(await screen.findByTitle<HTMLIFrameElement>("PDF 원본 PDF")).not.toBeNull();
    expect(getWorkspacePdfUrl).toHaveBeenCalledTimes(1);
    expect(getWorkspacePdfBlob).toHaveBeenCalledTimes(1);
    expect(createObjectURL).toHaveBeenCalledTimes(1);

    view.unmount();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:https://md2blog.test/pdf-original");
  });

  it("저장된 본문을 복원하되 비회원 페이지명은 임시 페이지로 유지한다", async () => {
    loadGuestDraft.mockResolvedValue({
      title: "잘못 저장된 파일명",
      markdown: "# 저장된 Markdown",
      updatedAt: 1,
    });

    renderPage();

    expect(await screen.findByDisplayValue("# 저장된 Markdown")).not.toBeNull();
    expect(screen.getByRole("button", { name: "임시 페이지" })).not.toBeNull();
    await waitFor(() => {
      expect(saveGuestDraft).toHaveBeenCalledWith({
        title: "임시 페이지",
        markdown: "# 저장된 Markdown",
        updatedAt: expect.any(Number),
      });
    });
  });

  it("본문을 수정하면 임시 페이지로 자동 저장한다", async () => {
    const user = userEvent.setup();
    renderPage();
    const editor = await screen.findByRole("textbox", { name: "Markdown 내용" });

    await user.clear(editor);
    await user.type(editor, "새 내용");

    await waitFor(() => {
      expect(saveGuestDraft).toHaveBeenLastCalledWith({
        title: "임시 페이지",
        markdown: "새 내용",
        updatedAt: expect.any(Number),
      });
    }, { timeout: 1500 });
  });

  it("비회원의 새 페이지 추가와 안내 링크는 로그인 화면으로 연결한다", async () => {
    renderPage();
    await screen.findByRole("textbox", { name: "Markdown 내용" });

    const addPageLink = screen.getByRole("link", { name: "새 페이지 추가" });
    expect(addPageLink.getAttribute("href")).toBe("/login");
    expect(addPageLink.getAttribute("data-tooltip")).toBe("페이지 추가");
    expect(screen.getByRole("link", { name: "내 기록장으로 옮기기" }).getAttribute("href")).toBe("/login");
  });

  it("비회원이 페이지 추가를 누르면 로그인 화면 이동 여부를 확인한다", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByRole("textbox", { name: "Markdown 내용" });

    await user.click(screen.getByRole("link", { name: "새 페이지 추가" }));

    expect(screen.getByRole("alertdialog")).not.toBeNull();
    expect(screen.getByText(/로그인 화면으로 이동하시겠습니까/)).not.toBeNull();
    await user.click(screen.getByRole("button", { name: "취소" }));
    expect(screen.getByRole("textbox", { name: "Markdown 내용" })).not.toBeNull();
  });

  it("구분선 방향키 조절과 더블 클릭 초기화를 지원하고 비율을 저장한다", async () => {
    vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function () {
      if (this.classList.contains("workspace-shell")) {
        return { left: 0, right: 1280, width: 1280, top: 0, bottom: 800, height: 800, x: 0, y: 0, toJSON: () => ({}) };
      }
      if (this.classList.contains("workspace-editor")) {
        return { left: 280, right: 755, width: 475, top: 0, bottom: 800, height: 800, x: 280, y: 0, toJSON: () => ({}) };
      }
      return { left: 0, right: 0, width: 0, top: 0, bottom: 0, height: 0, x: 0, y: 0, toJSON: () => ({}) };
    });
    renderPage();
    const divider = await screen.findByRole("separator", { name: "에디터와 미리보기 너비 조절" });

    fireEvent.keyDown(divider, { key: "ArrowRight" });

    await waitFor(() => expect(divider.getAttribute("aria-valuenow")).toBe("50"));
    expect(window.localStorage.getItem("md2blog-workspace-editor-ratio")).toBe("0.5");

    fireEvent.doubleClick(divider);
    await waitFor(() => expect(divider.getAttribute("aria-valuenow")).toBe("48"));
  });

  it("로그인 사용자는 서버 페이지를 불러오고 선택한 본문을 자동 저장한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      {
        id: "10",
        title: "개발 노트",
        content: "# 기존 본문",
        parent_id: null,
        sort_order: 0,
      },
    ]);
    getWorkspacePage.mockResolvedValue({
      id: "10",
      title: "개발 노트",
      contents: "# 기존 본문",
      parent_id: null,
      sort_order: 0,
    });
    const user = userEvent.setup();
    renderPage();

    const editor = await screen.findByDisplayValue("# 기존 본문");
    expect(screen.getByRole("region", { name: "페이지 목록" })).not.toBeNull();
    expect(screen.queryByText("현재 브라우저에 저장 중")).toBeNull();

    await user.clear(editor);
    await user.type(editor, "# 변경 본문");

    await waitFor(() => {
      expect(updateWorkspacePage).toHaveBeenLastCalledWith("10", {
        title: "개발 노트",
        content: "# 변경 본문",
      });
    }, { timeout: 1800 });
  });

  it("로그인 사용자는 최상위 페이지를 추가할 수 있다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => expect(listWorkspacePages).toHaveBeenCalled());

    await user.click(screen.getByRole("button", { name: "새 페이지 추가" }));

    expect(screen.getByRole("dialog", { name: "새 페이지" })).not.toBeNull();
    await user.type(screen.getByRole("textbox", { name: "제목" }), "새 페이지");
    await user.click(screen.getByRole("button", { name: "추가" }));

    await waitFor(() => {
      expect(createWorkspacePage).toHaveBeenCalledWith({
        title: "새 페이지",
        content: "",
        parent_id: null,
        type: "MARKDOWN",
      });
    });
    expect(await screen.findByRole("button", { name: "새 페이지" })).not.toBeNull();
  });

  it("HTML 파일을 가져와 HTML 페이지를 만든다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    createWorkspacePage.mockResolvedValue({
      id: "20",
      title: "intro",
      type: "HTML",
      contents: "<h1>소개</h1>",
      parent_id: null,
      sort_order: 0,
    });
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => expect(listWorkspacePages).toHaveBeenCalled());

    await user.click(screen.getByRole("button", { name: "새 페이지 추가" }));
    await user.click(screen.getByRole("radio", { name: /HTML/ }));
    const file = new File(["<h1>소개</h1>"], "intro.html", { type: "text/html" });
    Object.defineProperty(file, "text", { value: vi.fn().mockResolvedValue("<h1>소개</h1>") });
    await user.upload(screen.getByLabelText(/^파일 가져오기 \(선택\)/), file);
    expect((screen.getByRole("textbox", { name: "제목" }) as HTMLInputElement).value).toBe("intro");
    await user.click(screen.getByRole("button", { name: "추가" }));

    await waitFor(() => expect(createWorkspacePage).toHaveBeenCalledWith({
      title: "intro",
      content: "<h1>소개</h1>",
      parent_id: null,
      type: "HTML",
    }));
  });

  it("미리보기 없는 메모 페이지를 만든다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    createWorkspacePage.mockResolvedValue({
      id: "25",
      owner_id: "1",
      title: "회의 메모",
      type: "MEMO",
      contents: "",
      parent_id: null,
      sort_order: 0,
    });
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => expect(listWorkspacePages).toHaveBeenCalled());

    await user.click(screen.getByRole("button", { name: "새 페이지 추가" }));
    await user.click(screen.getByRole("radio", { name: /메모/ }));
    await user.type(screen.getByRole("textbox", { name: "제목" }), "회의 메모");
    expect(screen.queryByLabelText(/파일/)).toBeNull();
    await user.click(screen.getByRole("button", { name: "추가" }));

    await waitFor(() => expect(createWorkspacePage).toHaveBeenCalledWith({
      title: "회의 메모",
      content: "",
      parent_id: null,
      type: "MEMO",
    }));
    expect(await screen.findByRole("region", { name: "메모 편집기" })).not.toBeNull();
  });

  it("PDF 파일을 multipart 생성 API로 전달한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => expect(listWorkspacePages).toHaveBeenCalled());

    await user.click(screen.getByRole("button", { name: "새 페이지 추가" }));
    await user.click(screen.getByRole("radio", { name: /PDF/ }));
    const file = new File(["%PDF-1.7"], "document.pdf", { type: "application/pdf" });
    await user.upload(screen.getByLabelText(/^PDF 파일 \*/), file);
    await user.click(screen.getByRole("button", { name: "추가" }));

    await waitFor(() => expect(createPdfWorkspacePage).toHaveBeenCalledWith({
      title: "document",
      file,
      parent_id: null,
    }));
  });

  it("페이지 가운데에 드롭하면 하위 페이지로 이동한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "개발 노트", parent_id: null, sort_order: 0 },
      { id: "20", owner_id: "1", title: "API 설계", parent_id: null, sort_order: 1 },
    ]);
    const movement = createDeferred<{
      id: string;
      title: string;
      contents: string;
      parent_id: string;
      sort_order: number;
    }>();
    moveWorkspacePage.mockReturnValueOnce(movement.promise);
    renderPage();
    const source = (await screen.findByRole("button", { name: "API 설계" })).closest(".workspace-page-item");
    const target = screen.getByRole("button", { name: "개발 노트" }).closest(".workspace-page-item");
    expect(source).not.toBeNull();
    expect(target).not.toBeNull();
    vi.spyOn(target as HTMLElement, "getBoundingClientRect").mockReturnValue({
      top: 0, bottom: 40, height: 40, left: 0, right: 200, width: 200, x: 0, y: 0,
      toJSON: () => ({}),
    });
    const dataTransfer = {
      effectAllowed: "none",
      dropEffect: "none",
      setData: vi.fn(),
      getData: vi.fn(),
    };

    fireEvent.dragStart(source as HTMLElement, { dataTransfer });
    fireEvent.dragOver(target as HTMLElement, { dataTransfer, clientY: 20 });
    fireEvent.drop(target as HTMLElement, { dataTransfer, clientY: 20 });

    expect(screen.getByRole("button", { name: "개발 노트 하위 페이지 접기" })).not.toBeNull();
    expect(screen.getByRole("button", { name: "API 설계" })).not.toBeNull();
    await waitFor(() => {
      expect(moveWorkspacePage).toHaveBeenCalledWith("20", {
        parent_id: "10",
        sort_order: 0,
      });
    });
    movement.resolve({ id: "20", title: "API 설계", contents: "", parent_id: "10", sort_order: 0 });
  });

  it("페이지 이동 요청이 실패하면 원래 위치로 되돌린다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "개발 노트", parent_id: null, sort_order: 0 },
      { id: "20", owner_id: "1", title: "API 설계", parent_id: null, sort_order: 1 },
    ]);
    const movement = createDeferred<never>();
    moveWorkspacePage.mockReturnValueOnce(movement.promise);
    renderPage();
    const source = (await screen.findByRole("button", { name: "API 설계" })).closest(".workspace-page-item") as HTMLElement;
    const target = screen.getByRole("button", { name: "개발 노트" }).closest(".workspace-page-item") as HTMLElement;
    vi.spyOn(target, "getBoundingClientRect").mockReturnValue({
      top: 0, bottom: 40, height: 40, left: 0, right: 200, width: 200, x: 0, y: 0,
      toJSON: () => ({}),
    });
    const dataTransfer = { effectAllowed: "none", dropEffect: "none", setData: vi.fn(), getData: vi.fn() };

    fireEvent.dragStart(source, { dataTransfer });
    fireEvent.drop(target, { dataTransfer, clientY: 20 });
    expect(screen.getByRole("button", { name: "개발 노트 하위 페이지 접기" })).not.toBeNull();

    movement.reject(new Error("failed"));
    await screen.findByText("페이지를 이동하지 못했습니다.");
    expect(screen.getByRole("button", { name: "API 설계" })).not.toBeNull();
    expect(screen.getByRole("button", { name: "API 설계" }).closest(".workspace-page-item")?.style.paddingLeft).toBe("16px");
  });

  it("페이지 메뉴에서 이름을 변경한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "개발 노트", parent_id: null, sort_order: 0 },
    ]);
    updateWorkspacePage.mockResolvedValue({
      id: "10",
      title: "서버 설계",
      contents: "",
      parent_id: null,
      sort_order: 0,
    });
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "개발 노트 메뉴" }));
    await user.click(screen.getByRole("menuitem", { name: "이름 변경" }));
    const input = screen.getByRole("textbox", { name: "개발 노트 이름 변경" });
    await user.clear(input);
    await user.type(input, "서버 설계{Enter}");

    await waitFor(() => {
      expect(updateWorkspacePage).toHaveBeenCalledWith("10", { title: "서버 설계" });
    });
  });

  it("페이지 이름 툴팁 없이 하위 페이지 추가 버튼에만 툴팁을 제공한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      {
        id: "10",
        title: "아주 긴 페이지 이름 전체 내용",
        content: "",
        parent_id: null,
        sort_order: 0,
      },
    ]);
    renderPage();

    const pageButton = await screen.findByRole("button", { name: "아주 긴 페이지 이름 전체 내용" });
    expect(pageButton.getAttribute("title")).toBeNull();
    expect(pageButton.getAttribute("data-page-title")).toBeNull();
    const addButton = screen.getByRole("button", {
      name: "아주 긴 페이지 이름 전체 내용 하위 페이지 추가",
    });
    expect(addButton.getAttribute("data-tooltip")).toBe("하위 페이지 추가");
  });

  it("페이지 목록 하단에서는 페이지 메뉴를 위쪽으로 연다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "마지막 페이지", parent_id: null, sort_order: 0 },
    ]);
    const user = userEvent.setup();
    renderPage();

    const menuButton = await screen.findByRole("button", { name: "마지막 페이지 메뉴" });
    const pageList = screen.getByRole("region", { name: "페이지 목록" });
    vi.spyOn(pageList, "getBoundingClientRect").mockReturnValue({ top: 100, bottom: 500 } as DOMRect);
    vi.spyOn(menuButton, "getBoundingClientRect").mockReturnValue({ top: 455, bottom: 479 } as DOMRect);

    await user.click(menuButton);

    expect(screen.getByRole("menu").classList.contains("is-upward")).toBe(true);
  });

  it("페이지 메뉴를 바깥 클릭으로 닫은 뒤 호버해도 다시 열리지 않는다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "개발 노트", parent_id: null, sort_order: 0 },
    ]);
    const user = userEvent.setup();
    renderPage();

    const menuButton = await screen.findByRole("button", { name: "개발 노트 메뉴" });
    await user.click(menuButton);
    expect(screen.getByRole("menu")).not.toBeNull();

    fireEvent.pointerDown(document.body);
    expect(screen.queryByRole("menu")).toBeNull();
    fireEvent.mouseEnter(menuButton.closest(".workspace-page-item") as HTMLElement);
    expect(screen.queryByRole("menu")).toBeNull();
  });

  it("페이지 제목 바깥의 행을 클릭해도 해당 페이지를 선택한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "첫 페이지", parent_id: null, sort_order: 0 },
      { id: "20", owner_id: "1", title: "둘째 페이지", parent_id: null, sort_order: 1 },
    ]);
    getWorkspacePage.mockImplementation(async (pageId: string) => ({
      id: pageId,
      title: pageId === "10" ? "첫 페이지" : "둘째 페이지",
      contents: pageId === "10" ? "첫 내용" : "둘째 내용",
      parent_id: null,
      sort_order: pageId === "10" ? 0 : 1,
    }));
    renderPage();

    const secondPageButton = await screen.findByRole("button", { name: "둘째 페이지" });
    const secondPageRow = secondPageButton.closest(".workspace-page-item");
    fireEvent.click(secondPageRow as HTMLElement);

    expect(secondPageRow?.classList.contains("is-active")).toBe(true);
    await waitFor(() => {
      expect((screen.getByRole("textbox", { name: "Markdown 내용" }) as HTMLTextAreaElement).value).toBe("둘째 내용");
    });
  });

  it("페이지를 빠르게 전환해도 늦게 도착한 이전 응답이 현재 본문을 덮지 않는다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "첫 페이지", parent_id: null, sort_order: 0, type: "MARKDOWN" },
      { id: "20", owner_id: "1", title: "느린 페이지", parent_id: null, sort_order: 1, type: "MARKDOWN" },
      { id: "30", owner_id: "1", title: "현재 페이지", parent_id: null, sort_order: 2, type: "MARKDOWN" },
    ]);
    const slowPage = createDeferred<{
      id: string;
      title: string;
      contents: string;
      parent_id: null;
      sort_order: number;
      type: "MARKDOWN";
    }>();
    const currentPage = createDeferred<{
      id: string;
      title: string;
      contents: string;
      parent_id: null;
      sort_order: number;
      type: "MARKDOWN";
    }>();
    getWorkspacePage.mockImplementation((pageId: string) => {
      if (pageId === "20") return slowPage.promise;
      if (pageId === "30") return currentPage.promise;
      return Promise.resolve({
        id: "10",
        title: "첫 페이지",
        contents: "첫 내용",
        parent_id: null,
        sort_order: 0,
        type: "MARKDOWN",
      });
    });
    const user = userEvent.setup();
    renderPage();
    expect(await screen.findByDisplayValue("첫 내용")).not.toBeNull();

    await user.click(screen.getByRole("button", { name: "느린 페이지" }));
    await user.click(screen.getByRole("button", { name: "현재 페이지" }));
    currentPage.resolve({
      id: "30",
      title: "현재 페이지",
      contents: "현재 내용",
      parent_id: null,
      sort_order: 2,
      type: "MARKDOWN",
    });
    expect(await screen.findByDisplayValue("현재 내용")).not.toBeNull();

    slowPage.resolve({
      id: "20",
      title: "느린 페이지",
      contents: "늦게 도착한 이전 내용",
      parent_id: null,
      sort_order: 1,
      type: "MARKDOWN",
    });
    await waitFor(() => {
      expect((screen.getByRole("textbox", { name: "Markdown 내용" }) as HTMLTextAreaElement).value)
        .toBe("현재 내용");
    });
  });

  it("삭제 확인 문구는 실제 하위 페이지 존재 여부를 반영한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "개발 노트", parent_id: null, sort_order: 0 },
      { id: "20", owner_id: "1", title: "API 설계", parent_id: "10", sort_order: 0 },
    ]);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "개발 노트 하위 페이지 펼치기" }));
    await user.click(await screen.findByRole("button", { name: "API 설계 메뉴" }));
    await user.click(screen.getByRole("menuitem", { name: "휴지통" }));
    expect(screen.getByText("'API 설계' 페이지를 휴지통으로 이동할까요?")).not.toBeNull();
    await user.click(screen.getByRole("button", { name: "취소" }));

    await user.click(screen.getByRole("button", { name: "개발 노트 메뉴" }));
    await user.click(screen.getByRole("menuitem", { name: "휴지통" }));
    expect(screen.getByText("'개발 노트' 페이지와 모든 하위 페이지를 휴지통으로 이동할까요?")).not.toBeNull();
    await user.click(screen.getByRole("button", { name: "취소" }));
  });

  it("페이지 삭제 확인 직후 목록에서 제거하고 다음 페이지를 선택한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "삭제할 페이지", parent_id: null, sort_order: 0 },
      { id: "20", owner_id: "1", title: "다음 페이지", parent_id: null, sort_order: 1 },
    ]);
    const deletion = createDeferred<void>();
    deleteWorkspacePage.mockReturnValueOnce(deletion.promise);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "삭제할 페이지 메뉴" }));
    await user.click(screen.getByRole("menuitem", { name: "휴지통" }));
    await user.click(screen.getByRole("button", { name: "휴지통으로 이동" }));

    expect(screen.queryByRole("button", { name: "삭제할 페이지" })).toBeNull();
    expect(screen.getByRole("button", { name: "다음 페이지" }).closest(".workspace-page-item")?.classList.contains("is-active")).toBe(true);

    deletion.resolve();
    await waitFor(() => expect(deleteWorkspacePage).toHaveBeenCalledWith("10"));
  });

  it("페이지 삭제 요청이 실패하면 낙관적으로 제거한 페이지를 복원한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "삭제할 페이지", parent_id: null, sort_order: 0 },
      { id: "20", owner_id: "1", title: "다음 페이지", parent_id: null, sort_order: 1 },
    ]);
    const deletion = createDeferred<void>();
    deleteWorkspacePage.mockReturnValueOnce(deletion.promise);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "삭제할 페이지 메뉴" }));
    await user.click(screen.getByRole("menuitem", { name: "휴지통" }));
    await user.click(screen.getByRole("button", { name: "휴지통으로 이동" }));
    expect(screen.queryByRole("button", { name: "삭제할 페이지" })).toBeNull();

    deletion.reject(new Error("failed"));
    expect(await screen.findByRole("button", { name: "삭제할 페이지" })).not.toBeNull();
    expect(screen.getByText("페이지를 삭제하지 못했습니다.")).not.toBeNull();
  });

  it("휴지통 최상위 묶음은 최근 삭제 순이고 하위 페이지는 기존 순서를 유지한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([]);
    listTrashedWorkspacePages.mockResolvedValue([
      { id: "10", parent_id: null, title: "이전에 삭제", sort_order: 0, deleted_at: "2026-08-01T00:00:00Z", expires_at: "2026-08-31T00:00:00Z" },
      { id: "30", parent_id: null, title: "최근 삭제", sort_order: 5, deleted_at: "2026-09-01T00:00:00Z", expires_at: "2026-10-01T00:00:00Z" },
      { id: "31", parent_id: "30", title: "두 번째 하위", sort_order: 1, deleted_at: "2026-09-01T00:00:00Z", expires_at: "2026-10-01T00:00:00Z" },
      { id: "32", parent_id: "30", title: "첫 번째 하위", sort_order: 0, deleted_at: "2026-09-01T00:00:00Z", expires_at: "2026-10-01T00:00:00Z" },
    ]);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "휴지통" }));
    await waitFor(() => expect(getTrashedWorkspacePage).toHaveBeenCalledWith("30"));

    const recentPage = screen.getByRole("button", { name: "최근 삭제" });
    const olderPage = screen.getByRole("button", { name: "이전에 삭제" });
    expect(recentPage.compareDocumentPosition(olderPage) & Node.DOCUMENT_POSITION_FOLLOWING).not.toBe(0);
    expect(recentPage.querySelector(".workspace-page-child-count")?.textContent).toBe("2");
    expect(olderPage.querySelector(".workspace-page-child-count")).toBeNull();

    await user.click(screen.getByRole("button", { name: "최근 삭제 하위 페이지 펼치기" }));
    const firstChild = screen.getByRole("button", { name: "첫 번째 하위" });
    const secondChild = screen.getByRole("button", { name: "두 번째 하위" });
    expect(firstChild.compareDocumentPosition(secondChild) & Node.DOCUMENT_POSITION_FOLLOWING).not.toBe(0);
  });

  it("휴지통에 다시 들어가면 기존 목록을 유지한 채 갱신한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "1", owner_id: "1", title: "활성 페이지", parent_id: null, sort_order: 0 },
    ]);
    const refresh = createDeferred<Awaited<ReturnType<typeof listTrashedWorkspacePages>>>();
    listTrashedWorkspacePages
      .mockResolvedValueOnce([
        { id: "10", parent_id: null, title: "삭제한 페이지", sort_order: 0, deleted_at: "2026-09-01T00:00:00Z", expires_at: "2026-10-01T00:00:00Z" },
      ])
      .mockReturnValueOnce(refresh.promise);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "휴지통" }));
    expect(await screen.findByRole("button", { name: "삭제한 페이지" })).not.toBeNull();
    await user.click(screen.getByRole("button", { name: "페이지 목록으로 돌아가기" }));
    await user.click(screen.getByRole("button", { name: "휴지통" }));

    expect(screen.getByRole("button", { name: "삭제한 페이지" }).closest(".workspace-page-item")?.classList.contains("is-active")).toBe(true);
    expect(screen.queryByText("휴지통을 불러오는 중…")).toBeNull();

    refresh.resolve([]);
    expect(await screen.findByText("휴지통이 비어 있습니다.")).not.toBeNull();
  });

  it("휴지통 페이지에 마우스를 올리면 상세를 선로딩하고 선택 시 같은 요청을 재사용한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([]);
    listTrashedWorkspacePages.mockResolvedValue([
      { id: "10", parent_id: null, title: "첫 삭제 페이지", sort_order: 0, type: "MARKDOWN", deleted_at: "2026-09-02T00:00:00Z", expires_at: "2026-10-02T00:00:00Z" },
      { id: "20", parent_id: null, title: "둘째 삭제 페이지", sort_order: 1, type: "MARKDOWN", deleted_at: "2026-09-01T00:00:00Z", expires_at: "2026-10-01T00:00:00Z" },
    ]);
    const secondPage = createDeferred<{
      id: string;
      owner_id: string;
      title: string;
      type: "MARKDOWN";
      contents: string;
      parent_id: null;
      sort_order: number;
    }>();
    getTrashedWorkspacePage.mockImplementation((pageId: string) => pageId === "20"
      ? secondPage.promise
      : Promise.resolve({
        id: "10",
        owner_id: "1",
        title: "첫 삭제 페이지",
        type: "MARKDOWN",
        contents: "첫 삭제 내용",
        parent_id: null,
        sort_order: 0,
      }));
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "휴지통" }));
    await screen.findByDisplayValue("첫 삭제 내용");
    const secondPageRow = screen.getByRole("button", { name: "둘째 삭제 페이지" }).closest(".workspace-page-item") as HTMLElement;
    fireEvent.mouseEnter(secondPageRow);
    await waitFor(() => expect(getTrashedWorkspacePage).toHaveBeenCalledWith("20"));
    const clickPromise = user.click(secondPageRow);
    await waitFor(() => expect(secondPageRow.classList.contains("is-active")).toBe(true));
    expect(getTrashedWorkspacePage.mock.calls.filter(([pageId]) => pageId === "20")).toHaveLength(1);
    secondPage.resolve({
      id: "20",
      owner_id: "1",
      title: "둘째 삭제 페이지",
      type: "MARKDOWN",
      contents: "둘째 삭제 내용",
      parent_id: null,
      sort_order: 1,
    });
    await clickPromise;
    await screen.findByDisplayValue("둘째 삭제 내용");
    expect(getTrashedWorkspacePage.mock.calls.filter(([pageId]) => pageId === "20")).toHaveLength(1);
  });

  it("휴지통에서 삭제한 페이지를 조회하고 복원한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValueOnce([]);
    listTrashedWorkspacePages.mockResolvedValueOnce([
      {
        id: "10",
        parent_id: null,
        title: "삭제한 페이지",
        sort_order: 0,
        type: "MARKDOWN",
        deleted_at: "2026-08-01T00:00:00Z",
        expires_at: "2026-08-31T00:00:00Z",
      },
      {
        id: "20",
        parent_id: "10",
        title: "삭제한 하위 페이지",
        sort_order: 0,
        type: "PDF",
        deleted_at: "2026-08-01T00:00:00Z",
        expires_at: "2026-08-31T00:00:00Z",
      },
    ]);
    const restoration = createDeferred<void>();
    restoreWorkspacePage.mockReturnValueOnce(restoration.promise);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "휴지통" }));
    expect(screen.getByText("휴지통의 페이지는 30일 후 영구 삭제됩니다.")).toBeTruthy();
    expect(screen.getByRole("img", { name: "Markdown 문서" })).not.toBeNull();
    await waitFor(() => {
      expect(getTrashedWorkspacePage).toHaveBeenCalledWith("10");
      expect((screen.getByRole("textbox", { name: "Markdown 내용" }) as HTMLTextAreaElement).value)
        .toBe("# 삭제한 페이지");
    });
    expect((screen.getByRole("textbox", { name: "Markdown 내용" }) as HTMLTextAreaElement).readOnly).toBe(true);

    expect(screen.queryByRole("button", { name: "삭제한 하위 페이지" })).toBeNull();
    await user.click(screen.getByRole("button", { name: "삭제한 페이지 하위 페이지 펼치기" }));
    expect(screen.getByRole("button", { name: "삭제한 하위 페이지" })).not.toBeNull();
    expect(screen.queryByRole("button", { name: "삭제한 하위 페이지 하위 페이지 펼치기" })).toBeNull();
    expect(screen.getByRole("button", { name: "삭제한 하위 페이지" }).closest(".workspace-page-item")?.querySelector(".workspace-page-icon")).not.toBeNull();

    await user.click(screen.getByRole("button", { name: "삭제한 페이지 메뉴" }));
    await user.click(screen.getByRole("menuitem", { name: "영구 삭제" }));
    expect(screen.getByText(/'삭제한 페이지' 페이지와 모든 하위 페이지를 영구 삭제할까요/)).not.toBeNull();
    await user.click(screen.getByRole("button", { name: "취소" }));
    expect(permanentlyDeleteWorkspacePage).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "삭제한 페이지 메뉴" }));
    await user.click(screen.getByRole("menuitem", { name: "복원" }));
    expect(screen.getByText("'삭제한 페이지' 페이지와 모든 하위 페이지를 복원할까요?")).not.toBeNull();
    await user.click(screen.getByRole("button", { name: "복원" }));
    expect(restoreWorkspacePage).toHaveBeenCalledWith("10");
    expect(screen.queryByText("삭제한 페이지")).toBeNull();
    expect(screen.getByRole("region", { name: "휴지통 목록" })).toBeTruthy();
    expect(listWorkspacePages).toHaveBeenCalledTimes(1);
    expect(listTrashedWorkspacePages).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole("button", { name: "페이지 목록으로 돌아가기" }));
    expect(screen.getByText("삭제한 페이지")).toBeTruthy();
    expect(screen.getByRole("img", { name: "Markdown 문서" })).not.toBeNull();
    await user.click(screen.getByRole("button", { name: "삭제한 페이지 하위 페이지 펼치기" }));
    expect(screen.getByRole("img", { name: "PDF 문서" })).not.toBeNull();
    restoration.resolve(undefined);
    await waitFor(() => expect(screen.getByText("페이지를 복원했습니다.")).not.toBeNull());
  });

  it("영구 삭제를 즉시 반영하고 요청 실패 시 페이지를 복구한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([]);
    listTrashedWorkspacePages.mockResolvedValue([
      {
        id: "10",
        parent_id: null,
        title: "삭제한 페이지",
        sort_order: 0,
        type: "MARKDOWN",
        deleted_at: "2026-08-01T00:00:00Z",
        expires_at: "2026-08-31T00:00:00Z",
      },
    ]);
    const deletion = createDeferred<void>();
    permanentlyDeleteWorkspacePage.mockReturnValueOnce(deletion.promise);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "휴지통" }));
    await screen.findByRole("button", { name: "삭제한 페이지" });
    await user.click(screen.getByRole("button", { name: "삭제한 페이지 메뉴" }));
    await user.click(screen.getByRole("menuitem", { name: "영구 삭제" }));
    await user.click(screen.getByRole("button", { name: "영구 삭제" }));

    expect(permanentlyDeleteWorkspacePage).toHaveBeenCalledWith("10");
    expect(screen.queryByRole("button", { name: "삭제한 페이지" })).toBeNull();

    deletion.reject(new Error("delete failed"));
    await waitFor(() => expect(screen.getByText("페이지를 영구 삭제하지 못했습니다.")).not.toBeNull());
    expect(screen.getByRole("button", { name: "삭제한 페이지" })).not.toBeNull();
  });

  it("휴지통의 메모 페이지를 미리보기 없이 읽기 전용으로 표시한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([]);
    listTrashedWorkspacePages.mockResolvedValue([
      {
        id: "10",
        parent_id: null,
        title: "삭제한 메모",
        sort_order: 0,
        type: "MEMO",
        deleted_at: "2026-08-01T00:00:00Z",
        expires_at: "2026-08-31T00:00:00Z",
      },
    ]);
    getTrashedWorkspacePage.mockResolvedValue({
      id: "10",
      owner_id: "1",
      title: "삭제한 메모",
      type: "MEMO",
      contents: "삭제 전 메모",
      parent_id: null,
      sort_order: 0,
    });
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "휴지통" }));

    const editor = await screen.findByRole("textbox", { name: "메모 내용" });
    expect((editor as HTMLTextAreaElement).value).toBe("삭제 전 메모");
    expect((editor as HTMLTextAreaElement).readOnly).toBe(true);
    expect(screen.queryByRole("tab", { name: "미리보기" })).toBeNull();
    expect(screen.queryByRole("separator", { name: "에디터와 미리보기 너비 조절" })).toBeNull();
  });

  it("복원 요청이 실패하면 낙관적으로 이동한 페이지를 휴지통으로 되돌린다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([]);
    listTrashedWorkspacePages.mockResolvedValue([
      {
        id: "10",
        parent_id: null,
        title: "복원할 페이지",
        sort_order: 0,
        type: "MARKDOWN",
        deleted_at: "2026-08-01T00:00:00Z",
        expires_at: "2026-08-31T00:00:00Z",
      },
    ]);
    restoreWorkspacePage.mockRejectedValueOnce(new Error("restore failed"));
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "휴지통" }));
    await user.click(await screen.findByRole("button", { name: "복원할 페이지 메뉴" }));
    await user.click(screen.getByRole("menuitem", { name: "복원" }));
    await user.click(screen.getByRole("button", { name: "복원" }));

    await waitFor(() => expect(screen.getByText("페이지를 복원하지 못했습니다.")).not.toBeNull());
    expect(screen.getByRole("button", { name: "복원할 페이지" })).not.toBeNull();
    await user.click(screen.getByRole("button", { name: "페이지 목록으로 돌아가기" }));
    expect(screen.queryByRole("button", { name: "복원할 페이지" })).toBeNull();
  });

  it("페이지 검색 API 결과에 계층 경로를 표시하고 페이지를 선택한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1", email_verified: true } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", owner_id: "1", title: "개발 노트", parent_id: null, sort_order: 0 },
      { id: "20", owner_id: "1", title: "블로그 초안", parent_id: "10", sort_order: 0 },
    ]);
    searchWorkspacePages.mockResolvedValue([
      { id: "20", owner_id: "1", title: "블로그 초안", parent_id: "10", sort_order: 0 },
    ]);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "페이지 검색" }));
    expect(screen.getByText("개발 노트")).toBeTruthy();
    expect(screen.getByRole("button", { name: "새 페이지 추가" })).toBeTruthy();
    expect(screen.queryByText(/검색 결과/)).toBeNull();
    expect(searchWorkspacePages).not.toHaveBeenCalled();

    await user.type(screen.getByRole("searchbox", { name: "페이지 검색어" }), "블로그");

    await waitFor(() => expect(searchWorkspacePages).toHaveBeenCalledWith("블로그"));
    expect(screen.getByText("검색 결과 1")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "새 페이지 추가" })).toBeNull();
    expect(screen.queryByText("개발 노트")).toBeNull();
    expect(screen.getByText("개발 노트 › 블로그 초안")).toBeTruthy();
    await user.click(screen.getByRole("button", { name: /블로그 초안/ }));
    expect(getWorkspacePage).toHaveBeenCalledWith("20");
  });

});

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
  createWorkspacePage,
  updateWorkspacePage,
  deleteWorkspacePage,
  moveWorkspacePage,
} = vi.hoisted(() => ({
  convertMarkdown: vi.fn(),
  loadGuestDraft: vi.fn(),
  saveGuestDraft: vi.fn(),
  useAuth: vi.fn(),
  listWorkspacePages: vi.fn(),
  createWorkspacePage: vi.fn(),
  updateWorkspacePage: vi.fn(),
  deleteWorkspacePage: vi.fn(),
  moveWorkspacePage: vi.fn(),
}));

vi.mock("../../../src/shared/markdown/converter-core", () => ({ convertMarkdown }));
vi.mock("../../../src/pages/workspace/guest-draft-store", () => ({ loadGuestDraft, saveGuestDraft }));
vi.mock("../../../src/features/auth/AuthProvider", () => ({ useAuth }));
vi.mock("../../../src/features/workspace/api", () => ({
  listWorkspacePages,
  createWorkspacePage,
  updateWorkspacePage,
  deleteWorkspacePage,
  moveWorkspacePage,
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

function renderPage() {
  return render(
    <MemoryRouter>
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
    createWorkspacePage.mockResolvedValue({
      id: "10",
      title: "새 페이지",
      content: "# 새 페이지\n",
      parent_id: null,
      position: 0,
    });
    updateWorkspacePage.mockImplementation(async (id, input) => ({
      id,
      title: input.title ?? "페이지",
      content: input.content ?? "",
      parent_id: null,
      position: 0,
    }));
    deleteWorkspacePage.mockResolvedValue(undefined);
    moveWorkspacePage.mockImplementation(async (id, input) => ({
      id,
      title: "이동한 페이지",
      content: "",
      parent_id: input.parent_id,
      position: input.position,
    }));
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  it("로그인 상태 확인 중에는 임시 페이지를 표시하지 않는다", () => {
    useAuth.mockReturnValue({ status: "loading", user: null });

    renderPage();

    expect(screen.getByText("내 기록장을 불러오는 중…")).not.toBeNull();
    expect(screen.queryByText("임시 페이지")).toBeNull();
    expect(loadGuestDraft).not.toHaveBeenCalled();
  });

  it("회원 페이지 API 응답 전에도 임시 페이지를 표시하지 않는다", () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1" } });
    listWorkspacePages.mockReturnValue(new Promise(() => undefined));

    renderPage();

    expect(screen.getByText("내 기록장을 불러오는 중…")).not.toBeNull();
    expect(screen.queryByText("임시 페이지")).toBeNull();
    expect(loadGuestDraft).not.toHaveBeenCalled();
  });

  it("페이지 탭에서 임시 페이지를 선택하면 Markdown 탭으로 이동한다", async () => {
    const user = userEvent.setup();
    renderPage();

    expect(screen.getByRole("tab", { name: "페이지" }).getAttribute("aria-selected")).toBe("true");
    await user.click(screen.getByRole("button", { name: "임시 페이지" }));

    expect(screen.getByRole("tab", { name: "Markdown" }).getAttribute("aria-selected")).toBe("true");
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
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    const user = userEvent.setup();
    renderPage();
    await screen.findByRole("textbox", { name: "Markdown 내용" });

    await user.click(screen.getByRole("link", { name: "새 페이지 추가" }));

    expect(confirm).toHaveBeenCalledWith(
      "페이지를 추가하려면 로그인이 필요합니다.\n로그인 화면으로 이동하시겠습니까?",
    );
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
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1" } });
    listWorkspacePages.mockResolvedValue([
      {
        id: "10",
        title: "개발 노트",
        content: "# 기존 본문",
        parent_id: null,
        position: 0,
      },
    ]);
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
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1" } });
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => expect(listWorkspacePages).toHaveBeenCalled());

    await user.click(screen.getByRole("button", { name: "새 페이지 추가" }));

    await waitFor(() => {
      expect(createWorkspacePage).toHaveBeenCalledWith({
        title: "새 페이지",
        content: "# 새 페이지\n",
        parent_id: null,
      });
    });
    expect(await screen.findByRole("button", { name: "새 페이지" })).not.toBeNull();
  });

  it("페이지 가운데에 드롭하면 하위 페이지로 이동한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1" } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", title: "개발 노트", content: "", parent_id: null, position: 0 },
      { id: "20", title: "API 설계", content: "", parent_id: null, position: 1 },
    ]);
    moveWorkspacePage.mockResolvedValue({
      id: "20",
      title: "API 설계",
      content: "",
      parent_id: "10",
      position: 0,
    });
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

    await waitFor(() => {
      expect(moveWorkspacePage).toHaveBeenCalledWith("20", {
        parent_id: "10",
        position: 0,
      });
    });
  });

  it("페이지 메뉴에서 이름을 변경한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1" } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", title: "개발 노트", content: "", parent_id: null, position: 0 },
    ]);
    updateWorkspacePage.mockResolvedValue({
      id: "10",
      title: "서버 설계",
      content: "",
      parent_id: null,
      position: 0,
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
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1" } });
    listWorkspacePages.mockResolvedValue([
      {
        id: "10",
        title: "아주 긴 페이지 이름 전체 내용",
        content: "",
        parent_id: null,
        position: 0,
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
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1" } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", title: "마지막 페이지", content: "", parent_id: null, position: 0 },
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

  it("삭제 확인 문구는 실제 하위 페이지 존재 여부를 반영한다", async () => {
    useAuth.mockReturnValue({ status: "authenticated", user: { id: "1" } });
    listWorkspacePages.mockResolvedValue([
      { id: "10", title: "개발 노트", content: "", parent_id: null, position: 0 },
      { id: "20", title: "API 설계", content: "", parent_id: "10", position: 0 },
    ]);
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "API 설계 메뉴" }));
    await user.click(screen.getByRole("menuitem", { name: "삭제" }));
    expect(confirm).toHaveBeenLastCalledWith("'API 설계' 페이지를 삭제할까요?");

    await user.click(screen.getByRole("button", { name: "개발 노트 메뉴" }));
    await user.click(screen.getByRole("menuitem", { name: "삭제" }));
    expect(confirm).toHaveBeenLastCalledWith(
      "'개발 노트' 페이지와 모든 하위 페이지를 삭제할까요?",
    );
  });
});

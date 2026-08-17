import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("../../src/pages/markdown-paste/MarkdownPastePage", () => ({
  MarkdownPastePage: () => <main>빠른 변환 테스트 화면</main>,
}));

vi.mock("../../src/pages/workspace/WorkspaceGatePage", () => ({
  WorkspaceGatePage: () => <main>비회원 임시 페이지 편집 화면</main>,
}));

vi.mock("../../src/features/auth/AuthProvider", () => ({
  useAuth: () => ({
    status: "guest",
    user: null,
    login: vi.fn(),
    signup: vi.fn(),
    logout: vi.fn(),
  }),
}));

import { AppRoutes } from "../../src/app/router";

function renderRoute(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AppRoutes />
    </MemoryRouter>,
  );
}

describe("AppRoutes", () => {
  afterEach(cleanup);

  it("기본 경로에 빠른 변환 화면을 표시한다", () => {
    renderRoute("/");

    expect(screen.getByText("빠른 변환 테스트 화면")).not.toBeNull();
    expect(screen.getByRole("link", { name: "빠른 변환" }).getAttribute("aria-current")).toBe("page");
    expect(screen.queryByRole("link", { name: /MD2Blog/ })).toBeNull();
  });

  it("내 기록장 메뉴에서 비회원 임시 페이지를 표시한다", async () => {
    const user = userEvent.setup();
    renderRoute("/");

    await user.click(screen.getByRole("link", { name: /내 기록장/ }));

    expect(screen.getByText("비회원 임시 페이지 편집 화면")).not.toBeNull();
    expect(screen.getByRole("link", { name: "내 기록장" }).getAttribute("aria-current")).toBe("page");
  });

  it("로그인과 회원가입 경로를 직접 열 수 있다", () => {
    const { unmount } = renderRoute("/login");
    expect(screen.getByRole("heading", { name: "로그인" })).not.toBeNull();

    unmount();
    renderRoute("/signup");
    expect(screen.getByRole("heading", { name: "회원가입" })).not.toBeNull();
  });

  it("알 수 없는 경로에 404 화면을 표시한다", () => {
    renderRoute("/unknown-page");

    expect(screen.getByRole("heading", { name: "페이지를 찾을 수 없습니다" })).not.toBeNull();
  });

  it("구현되지 않은 개별 기록장 페이지 경로는 404 화면을 표시한다", () => {
    renderRoute("/workspace/123");

    expect(screen.getByRole("heading", { name: "페이지를 찾을 수 없습니다" })).not.toBeNull();
  });
});

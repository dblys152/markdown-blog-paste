import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

const auth = vi.hoisted(() => ({
  deleteAccount: vi.fn(),
  updateDisplayName: vi.fn(),
}));

vi.mock("../../src/features/auth/AuthProvider", () => ({
  useAuth: () => ({
    status: "authenticated",
    user: {
      id: "1",
      email: "user@example.com",
      display_name: "사용자",
      email_verified: true,
    },
    logout: vi.fn(),
    deleteAccount: auth.deleteAccount,
    updateDisplayName: auth.updateDisplayName,
  }),
}));

import { AppLayout } from "../../src/layouts/AppLayout";

describe("AppLayout 회원탈퇴", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("영구 삭제 경고와 비밀번호 재확인 후 회원탈퇴를 요청한다", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/workspace"]}>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="workspace" element={<main>기록장</main>} />
          </Route>
          <Route path="/" element={<main>빠른 변환</main>} />
        </Routes>
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("button", { name: /사용자/ }));
    await user.click(screen.getByRole("menuitem", { name: "계정 관리" }));
    expect(screen.getByText("user@example.com")).not.toBeNull();
    expect(screen.getByText("인증 완료")).not.toBeNull();
    await user.click(screen.getByRole("button", { name: "회원탈퇴" }));
    expect(screen.getByText(/즉시 영구 삭제되며 복구할 수 없습니다/)).not.toBeNull();

    await user.type(screen.getByLabelText("현재 비밀번호"), "password123");
    await user.click(screen.getByRole("button", { name: "영구 탈퇴" }));

    expect(auth.deleteAccount).toHaveBeenCalledWith("password123");
    expect(await screen.findByText("빠른 변환")).not.toBeNull();
  });

  it("계정 관리에서 닉네임을 변경한다", async () => {
    const user = userEvent.setup();
    auth.updateDisplayName.mockResolvedValue({
      id: "1",
      email: "user@example.com",
      display_name: "새 닉네임",
      email_verified: true,
    });
    render(
      <MemoryRouter initialEntries={["/workspace"]}>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="workspace" element={<main>기록장</main>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("button", { name: /사용자/ }));
    await user.click(screen.getByRole("menuitem", { name: "계정 관리" }));
    await user.click(screen.getByRole("button", { name: "닉네임 변경" }));
    const input = screen.getByRole("textbox", { name: "닉네임" });
    await user.clear(input);
    await user.type(input, "새 닉네임");
    await user.click(screen.getByRole("button", { name: "저장" }));

    expect(auth.updateDisplayName).toHaveBeenCalledWith("새 닉네임");
  });
});

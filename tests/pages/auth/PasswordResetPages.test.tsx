import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({
  requestPasswordReset: vi.fn(),
  confirmPasswordReset: vi.fn(),
}));

vi.mock("../../../src/features/auth/api", () => api);

import { ForgotPasswordPage } from "../../../src/pages/auth/ForgotPasswordPage";
import { ResetPasswordPage } from "../../../src/pages/auth/ResetPasswordPage";

describe("비밀번호 재설정 화면", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("이메일을 전송하고 계정 존재 여부를 드러내지 않는 안내를 표시한다", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <ForgotPasswordPage />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("이메일"), "user@example.com");
    await user.click(screen.getByRole("button", { name: "재설정 메일 보내기" }));

    expect(api.requestPasswordReset).toHaveBeenCalledWith("user@example.com");
    expect(await screen.findByText(/가입된 이메일이라면/)).not.toBeNull();
  });

  it("두 비밀번호가 일치하면 토큰으로 변경을 요청한다", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/reset-password?token=reset-token"]}>
        <Routes>
          <Route path="reset-password" element={<ResetPasswordPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("새 비밀번호"), "new-password");
    await user.type(screen.getByLabelText("새 비밀번호 확인"), "new-password");
    await user.click(screen.getByRole("button", { name: "비밀번호 변경" }));

    expect(api.confirmPasswordReset).toHaveBeenCalledWith("reset-token", "new-password");
    expect(await screen.findByRole("heading", { name: "비밀번호 변경 완료" })).not.toBeNull();
  });

  it("두 비밀번호가 다르면 변경 요청을 보내지 않는다", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/reset-password?token=reset-token"]}>
        <Routes>
          <Route path="reset-password" element={<ResetPasswordPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("새 비밀번호"), "new-password");
    await user.type(screen.getByLabelText("새 비밀번호 확인"), "other-password");
    await user.click(screen.getByRole("button", { name: "비밀번호 변경" }));

    expect(screen.getByRole("alert").textContent).toContain("일치하지 않습니다");
    expect(api.confirmPasswordReset).not.toHaveBeenCalled();
  });
});

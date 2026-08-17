import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

const auth = vi.hoisted(() => ({
  login: vi.fn(),
  signup: vi.fn(),
}));

vi.mock("../../../src/features/auth/AuthProvider", () => ({
  useAuth: () => ({
    status: "guest",
    user: null,
    login: auth.login,
    signup: auth.signup,
    logout: vi.fn(),
  }),
}));

import { LoginPage } from "../../../src/pages/auth/LoginPage";
import { SignupPage } from "../../../src/pages/auth/SignupPage";

function renderPage(page: "login" | "signup") {
  return render(
    <MemoryRouter initialEntries={[`/${page}`]}>
      <Routes>
        <Route path="login" element={<LoginPage />} />
        <Route path="signup" element={<SignupPage />} />
        <Route path="workspace" element={<main>기록장 화면</main>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("인증 화면", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("로그인 정보를 전송하고 기록장으로 이동한다", async () => {
    const user = userEvent.setup();
    renderPage("login");

    await user.type(screen.getByLabelText("이메일"), "user@example.com");
    await user.type(screen.getByLabelText("비밀번호"), "password123");
    await user.click(screen.getByRole("button", { name: "로그인" }));

    expect(auth.login).toHaveBeenCalledWith({
      email: "user@example.com",
      password: "password123",
    });
    expect(await screen.findByText("기록장 화면")).not.toBeNull();
  });

  it("회원가입 정보를 백엔드 필드명으로 전송한다", async () => {
    const user = userEvent.setup();
    renderPage("signup");

    await user.type(screen.getByLabelText("이름"), "사용자");
    await user.type(screen.getByLabelText("이메일"), "user@example.com");
    await user.type(screen.getByLabelText("비밀번호"), "password123");
    await user.click(screen.getByRole("button", { name: "회원가입" }));

    expect(auth.signup).toHaveBeenCalledWith({
      display_name: "사용자",
      email: "user@example.com",
      password: "password123",
    });
    expect(await screen.findByText("기록장 화면")).not.toBeNull();
  });
});

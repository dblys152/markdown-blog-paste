import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

const auth = vi.hoisted(() => ({
  login: vi.fn(),
  signup: vi.fn(),
  requestEmailVerification: vi.fn(),
  confirmEmailVerification: vi.fn(),
  refreshCurrentUser: vi.fn(),
  googleLogin: vi.fn(),
  googleSignup: vi.fn(),
  linkGoogleAndLogin: vi.fn(),
}));

vi.mock("../../../src/features/auth/AuthProvider", () => ({
  useAuth: () => ({
    status: "guest",
    user: null,
    login: auth.login,
    signup: auth.signup,
    requestEmailVerification: auth.requestEmailVerification,
    confirmEmailVerification: auth.confirmEmailVerification,
    refreshCurrentUser: auth.refreshCurrentUser,
    googleLogin: auth.googleLogin,
    googleSignup: auth.googleSignup,
    linkGoogleAndLogin: auth.linkGoogleAndLogin,
    logout: vi.fn(),
  }),
}));

vi.mock("../../../src/features/auth/GoogleIdentityButton", () => ({
  GoogleIdentityButton: ({ onCredential }: { onCredential: (credential: string) => void }) => (
    <button type="button" onClick={() => onCredential("google-credential")}>Google로 로그인</button>
  ),
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
        <Route path="verify-email" element={<main>이메일 인증 화면</main>} />
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

    await user.type(screen.getByLabelText("닉네임"), "사용자");
    await user.type(screen.getByLabelText("이메일"), "user@example.com");
    await user.type(screen.getByLabelText("비밀번호"), "password123");
    await user.click(screen.getByRole("button", { name: "회원가입" }));

    expect(auth.signup).toHaveBeenCalledWith({
      display_name: "사용자",
      email: "user@example.com",
      password: "password123",
    });
    expect(await screen.findByText("이메일 인증 화면")).not.toBeNull();
  });

  it("신규 Google 사용자는 닉네임을 입력해 가입한다", async () => {
    auth.googleLogin.mockResolvedValue({ status: "signup_required", email: "new@example.com" });
    const user = userEvent.setup();
    renderPage("login");

    await user.click(screen.getByRole("button", { name: "Google로 로그인" }));
    expect(await screen.findByText("new@example.com")).not.toBeNull();
    await user.type(screen.getByLabelText("닉네임"), "새사용자");
    await user.click(screen.getByRole("button", { name: "가입하고 로그인" }));

    expect(auth.googleSignup).toHaveBeenCalledWith("google-credential", "새사용자");
    expect(await screen.findByText("기록장 화면")).not.toBeNull();
  });

  it("기존 이메일 사용자는 비밀번호 확인 후 Google 계정을 연결한다", async () => {
    auth.googleLogin.mockResolvedValue({ status: "link_required", email: "user@example.com" });
    const user = userEvent.setup();
    renderPage("login");

    await user.click(screen.getByRole("button", { name: "Google로 로그인" }));
    await user.type(await screen.findByLabelText("기존 계정 비밀번호"), "password123");
    await user.click(screen.getByRole("button", { name: "연결하고 로그인" }));

    expect(auth.linkGoogleAndLogin).toHaveBeenCalledWith("google-credential", "password123");
  });
});

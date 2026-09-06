import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

const auth = vi.hoisted(() => ({
  state: {
    status: "authenticated",
    user: {
      id: "1",
      email: "user@example.com",
      display_name: "사용자",
      email_verified: false,
    },
  },
  requestEmailVerification: vi.fn(),
  confirmEmailVerification: vi.fn(),
  refreshCurrentUser: vi.fn(),
}));

vi.mock("../../../src/features/auth/AuthProvider", () => ({
  useAuth: () => ({
    ...auth.state,
    requestEmailVerification: auth.requestEmailVerification,
    confirmEmailVerification: auth.confirmEmailVerification,
    refreshCurrentUser: auth.refreshCurrentUser,
  }),
}));

import { VerifyEmailPage } from "../../../src/pages/auth/VerifyEmailPage";

function renderPage(entry = "/verify-email") {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>
        <Route path="verify-email" element={<VerifyEmailPage />} />
        <Route path="login" element={<main>로그인 화면</main>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("이메일 인증 화면", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    auth.state.status = "authenticated";
    auth.state.user.email_verified = false;
  });

  it("인증 메일 재발송을 요청한다", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: "인증 메일 다시 보내기" }));

    expect(auth.requestEmailVerification).toHaveBeenCalledOnce();
    expect(await screen.findByText("인증 메일을 다시 보냈습니다.")).not.toBeNull();
  });

  it("URL의 인증 토큰을 확인하고 완료 상태를 표시한다", async () => {
    auth.confirmEmailVerification.mockResolvedValue({ ...auth.state.user, email_verified: true });

    renderPage("/verify-email?token=verification-token");

    await waitFor(() => expect(auth.confirmEmailVerification).toHaveBeenCalledWith("verification-token"));
    expect(await screen.findByRole("heading", { name: "인증이 완료되었습니다" })).not.toBeNull();
    expect(screen.getByRole("link", { name: "내 기록장 열기" })).not.toBeNull();
  });

  it("인증 대기 탭이 다시 활성화되면 사용자 정보를 갱신한다", async () => {
    renderPage();

    window.dispatchEvent(new Event("focus"));

    await waitFor(() => expect(auth.refreshCurrentUser).toHaveBeenCalledOnce());
  });
});

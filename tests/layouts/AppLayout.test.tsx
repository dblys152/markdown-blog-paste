import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const auth = vi.hoisted(() => ({
  deleteAccount: vi.fn(),
  deleteGoogleAccount: vi.fn(),
  updateDisplayName: vi.fn(),
}));
const googleApi = vi.hoisted(() => ({
  getGoogleConnection: vi.fn(),
  connectGoogle: vi.fn(),
  disconnectGoogle: vi.fn(),
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
    deleteGoogleAccount: auth.deleteGoogleAccount,
    updateDisplayName: auth.updateDisplayName,
  }),
}));

vi.mock("../../src/features/auth/api", () => googleApi);
vi.mock("../../src/features/auth/GoogleIdentityButton", () => ({
  GoogleIdentityButton: ({ onCredential }: { onCredential: (credential: string) => void }) => (
    <button type="button" onClick={() => onCredential("google-credential")}>Google 계정으로 계속</button>
  ),
}));

import { AppLayout } from "../../src/layouts/AppLayout";

describe("AppLayout 회원탈퇴", () => {
  beforeEach(() => {
    googleApi.getGoogleConnection.mockResolvedValue({
      connected: false,
      email: null,
      can_disconnect: false,
    });
  });

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
    expect(screen.getByText(/모든 데이터가 영구 삭제되고/)).not.toBeNull();

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

  it("Google 연결 상태는 계정 관리 최초 진입에만 조회한다", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/workspace"]}>
        <Routes><Route element={<AppLayout />}><Route path="workspace" element={<main>기록장</main>} /></Route></Routes>
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("button", { name: /사용자/ }));
    await user.click(screen.getByRole("menuitem", { name: "계정 관리" }));
    expect(await screen.findByRole("button", { name: "Google 계정으로 계속" })).not.toBeNull();
    await user.click(screen.getByRole("button", { name: "계정 관리 닫기" }));
    await user.click(screen.getByRole("button", { name: /사용자/ }));
    await user.click(screen.getByRole("menuitem", { name: "계정 관리" }));

    expect(googleApi.getGoogleConnection).toHaveBeenCalledTimes(1);
  });

  it("비밀번호 로그인 수단이 남은 경우에만 Google 연결 해제를 노출한다", async () => {
    googleApi.getGoogleConnection.mockResolvedValueOnce({
      connected: true,
      email: "user@gmail.com",
      can_disconnect: true,
    });
    const user = userEvent.setup();
    const view = render(
      <MemoryRouter initialEntries={["/workspace"]}>
        <Routes><Route element={<AppLayout />}><Route path="workspace" element={<main>기록장</main>} /></Route></Routes>
      </MemoryRouter>,
    );
    await user.click(screen.getByRole("button", { name: /사용자/ }));
    await user.click(screen.getByRole("menuitem", { name: "계정 관리" }));
    expect(await screen.findByRole("button", { name: "연결 해제" })).not.toBeNull();

    view.unmount();
    googleApi.getGoogleConnection.mockResolvedValueOnce({
      connected: true,
      email: "google-only@gmail.com",
      can_disconnect: false,
    });
    render(
      <MemoryRouter initialEntries={["/workspace"]}>
        <Routes><Route element={<AppLayout />}><Route path="workspace" element={<main>기록장</main>} /></Route></Routes>
      </MemoryRouter>,
    );
    await user.click(screen.getByRole("button", { name: /사용자/ }));
    await user.click(screen.getByRole("menuitem", { name: "계정 관리" }));
    expect(await screen.findByText("google-only@gmail.com")).not.toBeNull();
    expect(screen.queryByRole("button", { name: "연결 해제" })).toBeNull();
  });

  it("Google 전용 계정은 Google 재인증과 최종 확인 후 탈퇴한다", async () => {
    googleApi.getGoogleConnection.mockResolvedValueOnce({
      connected: true,
      email: "google-only@gmail.com",
      can_disconnect: false,
    });
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/workspace"]}>
        <Routes>
          <Route element={<AppLayout />}><Route path="workspace" element={<main>기록장</main>} /></Route>
          <Route path="/" element={<main>빠른 변환</main>} />
        </Routes>
      </MemoryRouter>,
    );
    await user.click(screen.getByRole("button", { name: /사용자/ }));
    await user.click(screen.getByRole("menuitem", { name: "계정 관리" }));
    await screen.findByText("google-only@gmail.com");
    await user.click(screen.getByRole("button", { name: "회원탈퇴" }));
    expect(screen.queryByLabelText("현재 비밀번호")).toBeNull();
    await user.click(screen.getByRole("button", { name: "Google 계정으로 계속" }));

    expect(auth.deleteGoogleAccount).not.toHaveBeenCalled();
    expect(screen.getByText("본인 확인 완료")).not.toBeNull();
    await user.click(screen.getByRole("button", { name: "영구 탈퇴" }));

    expect(auth.deleteGoogleAccount).toHaveBeenCalledWith("google-credential");
  });
});

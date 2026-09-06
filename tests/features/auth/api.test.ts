import { afterEach, describe, expect, it, vi } from "vitest";
import {
  clearAccessToken,
  deleteAccount,
  getAccessToken,
  login,
  logout,
  confirmEmailVerification,
  confirmPasswordReset,
  requestEmailVerification,
  requestPasswordReset,
  restoreSession,
  updateDisplayName,
} from "../../../src/features/auth/api";

const SESSION = {
  access_token: "access-token",
  token_type: "bearer" as const,
  user: {
    id: "123",
    email: "user@example.com",
    display_name: "User",
    email_verified: true,
  },
};

describe("auth api", () => {
  afterEach(() => {
    clearAccessToken();
    vi.unstubAllGlobals();
  });

  it("로그인 요청에 쿠키를 포함하고 액세스 토큰을 메모리에 보관한다", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(SESSION), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await login({ email: "user@example.com", password: "password123" });

    expect(getAccessToken()).toBe("access-token");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/auth/login",
      expect.objectContaining({ method: "POST", credentials: "include" }),
    );
  });

  it("동시에 세션을 복원해도 refresh 요청은 한 번만 보낸다", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(SESSION), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const [first, second] = await Promise.all([restoreSession(), restoreSession()]);

    expect(first).toEqual(SESSION);
    expect(second).toEqual(SESSION);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("로그아웃 성공 후 메모리의 액세스 토큰을 제거한다", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify(SESSION), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);
    await login({ email: "user@example.com", password: "password123" });

    await logout();

    expect(getAccessToken()).toBeNull();
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://localhost:8000/auth/logout",
      expect.objectContaining({ method: "POST", credentials: "include" }),
    );
  });

  it("인증 메일을 요청할 때 액세스 토큰을 전달한다", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(SESSION), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);
    await login({ email: "user@example.com", password: "password123" });

    await requestEmailVerification();

    const headers = fetchMock.mock.calls[1][1]?.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer access-token");
  });

  it("이메일 인증 토큰을 확인한다", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(SESSION.user), { status: 200, headers: { "Content-Type": "application/json" } }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(confirmEmailVerification("verification-token")).resolves.toEqual(SESSION.user);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/auth/email-verification/confirm",
      expect.objectContaining({ method: "POST", body: JSON.stringify({ token: "verification-token" }) }),
    );
  });

  it("회원탈퇴 후 메모리의 액세스 토큰을 제거한다", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify(SESSION), { status: 200, headers: { "Content-Type": "application/json" } }),
      )
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);
    await login({ email: "user@example.com", password: "password123" });

    await deleteAccount("password123");

    expect(getAccessToken()).toBeNull();
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://localhost:8000/auth/account",
      expect.objectContaining({ method: "DELETE", body: JSON.stringify({ password: "password123" }) }),
    );
  });

  it("닉네임 변경 요청에 액세스 토큰을 전달한다", async () => {
    const updatedUser = { ...SESSION.user, display_name: "새 닉네임" };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify(SESSION), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(updatedUser), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    await login({ email: "user@example.com", password: "password123" });

    await expect(updateDisplayName("새 닉네임")).resolves.toEqual(updatedUser);

    const headers = fetchMock.mock.calls[1][1]?.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer access-token");
    expect(fetchMock.mock.calls[1][1]).toEqual(
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({ display_name: "새 닉네임" }),
      }),
    );
  });

  it("비밀번호 재설정 메일을 요청한다", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await requestPasswordReset("user@example.com");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/auth/password-reset/request",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ email: "user@example.com" }),
      }),
    );
  });

  it("새 비밀번호를 설정한다", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await confirmPasswordReset("reset-token", "new-password");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/auth/password-reset/confirm",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ token: "reset-token", new_password: "new-password" }),
      }),
    );
  });
});

import { afterEach, describe, expect, it, vi } from "vitest";
import {
  clearAccessToken,
  getAccessToken,
  login,
  logout,
  restoreSession,
} from "../../../src/features/auth/api";

const SESSION = {
  access_token: "access-token",
  token_type: "bearer" as const,
  user: {
    id: "123",
    email: "user@example.com",
    display_name: "User",
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
});

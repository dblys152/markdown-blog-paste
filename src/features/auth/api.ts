import { apiRequest } from "../../shared/api/http";

export type AuthUser = {
  id: string;
  email: string;
  display_name: string;
};

export type AuthSession = {
  access_token: string;
  token_type: "bearer";
  user: AuthUser;
};

export type LoginInput = {
  email: string;
  password: string;
};

export type SignupInput = LoginInput & {
  display_name: string;
};

let accessToken: string | null = null;
let refreshPromise: Promise<AuthSession | null> | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

function rememberSession(session: AuthSession): AuthSession {
  accessToken = session.access_token;
  return session;
}

export function clearAccessToken(): void {
  accessToken = null;
}

export async function login(input: LoginInput): Promise<AuthSession> {
  return rememberSession(
    await apiRequest<AuthSession>("/auth/login", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  );
}

export async function signup(input: SignupInput): Promise<AuthSession> {
  return rememberSession(
    await apiRequest<AuthSession>("/auth/signup", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  );
}

export function restoreSession(): Promise<AuthSession | null> {
  if (!refreshPromise) {
    refreshPromise = apiRequest<AuthSession>("/auth/refresh", { method: "POST" })
      .then(rememberSession)
      .catch(() => {
        clearAccessToken();
        return null;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

export async function logout(): Promise<void> {
  try {
    await apiRequest<void>("/auth/logout", { method: "POST" });
  } finally {
    clearAccessToken();
  }
}

export async function authenticatedRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const request = async (): Promise<T> => {
    const headers = new Headers(init.headers);
    if (accessToken) {
      headers.set("Authorization", `Bearer ${accessToken}`);
    }
    return apiRequest<T>(path, { ...init, headers });
  };

  try {
    return await request();
  } catch (error) {
    if (!(error instanceof Error) || !("status" in error) || error.status !== 401) {
      throw error;
    }
    const session = await restoreSession();
    if (!session) {
      throw error;
    }
    return request();
  }
}

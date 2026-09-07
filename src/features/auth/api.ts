import { apiRequest } from "../../shared/api/http";

export type AuthUser = {
  id: string;
  email: string;
  display_name: string;
  email_verified: boolean;
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

export type GoogleLoginFlow =
  | AuthSession
  | { status: "link_required" | "signup_required"; email: string };

export type GoogleConnection = {
  connected: boolean;
  email: string | null;
  can_disconnect: boolean;
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

export async function googleLogin(credential: string): Promise<GoogleLoginFlow> {
  const result = await apiRequest<GoogleLoginFlow>("/auth/google/login", {
    method: "POST",
    body: JSON.stringify({ credential }),
  });
  return "access_token" in result ? rememberSession(result) : result;
}

export async function googleSignup(credential: string, displayName: string): Promise<AuthSession> {
  return rememberSession(await apiRequest<AuthSession>("/auth/google/signup", {
    method: "POST",
    body: JSON.stringify({ credential, display_name: displayName }),
  }));
}

export async function linkGoogleAndLogin(credential: string, password: string): Promise<AuthSession> {
  return rememberSession(await apiRequest<AuthSession>("/auth/google/link-and-login", {
    method: "POST",
    body: JSON.stringify({ credential, password }),
  }));
}

export async function getGoogleConnection(): Promise<GoogleConnection> {
  return authenticatedRequest<GoogleConnection>("/auth/google/connection");
}

export async function connectGoogle(credential: string): Promise<void> {
  await authenticatedRequest<void>("/auth/google/connection", {
    method: "POST",
    body: JSON.stringify({ credential }),
  });
}

export async function disconnectGoogle(): Promise<void> {
  await authenticatedRequest<void>("/auth/google/connection", { method: "DELETE" });
}

export async function requestEmailVerification(): Promise<void> {
  await authenticatedRequest<void>("/auth/email-verification/request", { method: "POST" });
}

export async function confirmEmailVerification(token: string): Promise<AuthUser> {
  return apiRequest<AuthUser>("/auth/email-verification/confirm", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

export async function requestPasswordReset(email: string): Promise<void> {
  await apiRequest<void>("/auth/password-reset/request", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function confirmPasswordReset(token: string, newPassword: string): Promise<void> {
  await apiRequest<void>("/auth/password-reset/confirm", {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  clearAccessToken();
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

export async function deleteAccount(password: string): Promise<void> {
  await authenticatedRequest<void>("/auth/account", {
    method: "DELETE",
    body: JSON.stringify({ password }),
  });
  clearAccessToken();
}

export async function deleteGoogleAccount(credential: string): Promise<void> {
  await authenticatedRequest<void>("/auth/account", {
    method: "DELETE",
    body: JSON.stringify({ google_credential: credential }),
  });
  clearAccessToken();
}

export async function updateDisplayName(displayName: string): Promise<AuthUser> {
  return authenticatedRequest<AuthUser>("/auth/me", {
    method: "PATCH",
    body: JSON.stringify({ display_name: displayName }),
  });
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

import { API_BASE_URL } from "../config/env";

export type FieldError = {
  field: string;
  reason: string;
};

type ErrorBody = {
  code?: string;
  message?: string;
  errors?: FieldError[];
};

export class ApiError extends Error {
  readonly status: number;
  readonly code: string | null;
  readonly errors: FieldError[];

  constructor(status: number, body: ErrorBody) {
    super(body.message || "요청을 처리하지 못했습니다.");
    this.name = "ApiError";
    this.status = status;
    this.code = body.code ?? null;
    this.errors = body.errors ?? [];
  }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    let body: ErrorBody = {};
    try {
      body = (await response.json()) as ErrorBody;
    } catch {
      // JSON이 아닌 오류 응답에도 동일한 사용자 메시지를 사용한다.
    }
    throw new ApiError(response.status, body);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

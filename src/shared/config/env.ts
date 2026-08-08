const LOCAL_API_BASE_URL = "http://localhost:8000";

export function resolveApiBaseUrl(value: string | undefined): string {
  const candidate = value?.trim() || LOCAL_API_BASE_URL;
  let url: URL;

  try {
    url = new URL(candidate);
  } catch {
    throw new Error("VITE_API_BASE_URL은 올바른 URL이어야 합니다.");
  }

  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error("VITE_API_BASE_URL은 http:// 또는 https:// 주소여야 합니다.");
  }

  return url.href.replace(/\/$/, "");
}

export const API_BASE_URL = resolveApiBaseUrl(import.meta.env.VITE_API_BASE_URL);

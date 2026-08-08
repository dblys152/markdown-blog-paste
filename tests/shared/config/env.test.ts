import { describe, expect, it } from "vitest";
import { resolveApiBaseUrl } from "../../../src/shared/config/env";

describe("resolveApiBaseUrl", () => {
  it("설정이 없으면 로컬 FastAPI 주소를 사용한다", () => {
    expect(resolveApiBaseUrl(undefined)).toBe("http://localhost:8000");
  });

  it("주소 끝의 슬래시를 제거한다", () => {
    expect(resolveApiBaseUrl(" https://api.example.com/ ")).toBe("https://api.example.com");
  });

  it("HTTP가 아닌 프로토콜을 거부한다", () => {
    expect(() => resolveApiBaseUrl("ftp://api.example.com")).toThrow(
      "VITE_API_BASE_URL은 http:// 또는 https:// 주소여야 합니다.",
    );
  });

  it("잘못된 URL을 거부한다", () => {
    expect(() => resolveApiBaseUrl("not-a-url")).toThrow(
      "VITE_API_BASE_URL은 올바른 URL이어야 합니다.",
    );
  });
});

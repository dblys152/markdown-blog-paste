import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useHtmlPreviewDocument } from "../../../src/pages/workspace/useHtmlPreviewDocument";

describe("useHtmlPreviewDocument", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("마지막 입력 이후 250ms가 지났을 때만 HTML 미리보기를 갱신한다", () => {
    const { result, rerender } = renderHook(
      ({ source }) => useHtmlPreviewDocument(source, "pages:10", true),
      { initialProps: { source: "<p>처음</p>" } },
    );

    act(() => vi.advanceTimersByTime(200));
    expect(result.current).toBe("");
    rerender({ source: "<p>최종</p>" });
    act(() => vi.advanceTimersByTime(249));
    expect(result.current).toBe("");
    act(() => vi.advanceTimersByTime(1));

    expect(result.current).toContain("<p>최종</p>");
    expect(result.current).not.toContain("<p>처음</p>");
  });

  it("페이지를 전환하면 이전 HTML을 노출하지 않고 보류 중인 갱신을 취소한다", () => {
    const { result, rerender } = renderHook(
      ({ source, documentKey, enabled }) => useHtmlPreviewDocument(source, documentKey, enabled),
      { initialProps: { source: "<p>첫 페이지</p>", documentKey: "pages:10", enabled: true } },
    );
    act(() => vi.advanceTimersByTime(250));
    expect(result.current).toContain("첫 페이지");

    rerender({ source: "<p>둘째 페이지</p>", documentKey: "pages:20", enabled: true });
    expect(result.current).toBe("");
    rerender({ source: "", documentKey: "pages:20", enabled: false });
    act(() => vi.advanceTimersByTime(250));

    expect(result.current).toBe("");
  });
});

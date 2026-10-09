import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { getWorkspacePdfBlob, getWorkspacePdfUrl } = vi.hoisted(() => ({
  getWorkspacePdfBlob: vi.fn(),
  getWorkspacePdfUrl: vi.fn(),
}));

vi.mock("../../../src/features/workspace/api", () => ({
  getWorkspacePdfBlob,
  getWorkspacePdfUrl,
}));

import { useWorkspacePdfPreview } from "../../../src/pages/workspace/useWorkspacePdfPreview";

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((resolvePromise) => {
    resolve = resolvePromise;
  });
  return { promise, resolve };
}

describe("useWorkspacePdfPreview", () => {
  const createObjectURL = vi.fn((blob: Blob) => `blob:test/${blob.size}/${createObjectURL.mock.calls.length}`);
  const revokeObjectURL = vi.fn();
  const onError = vi.fn();

  beforeEach(() => {
    getWorkspacePdfUrl.mockImplementation(async (pageId: string) => ({
      url: `/workspace/pages/${pageId}/pdf/content`,
      expires_in: "900",
    }));
    getWorkspacePdfBlob.mockImplementation(async (path: string) => new Blob([path], { type: "application/pdf" }));
    class MockURL extends URL {}
    MockURL.createObjectURL = createObjectURL;
    MockURL.revokeObjectURL = revokeObjectURL;
    vi.stubGlobal("URL", MockURL);
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.unstubAllGlobals();
  });

  it("PDF 전환 중에는 이전 PDF URL을 노출하지 않는다", async () => {
    const secondUrl = createDeferred<{ url: string; expires_in: string }>();
    getWorkspacePdfUrl.mockImplementation((pageId: string) => pageId === "2"
      ? secondUrl.promise
      : Promise.resolve({ url: "/workspace/pages/1/pdf/content", expires_in: "900" }));
    const { result, rerender } = renderHook(
      ({ pageId }) => useWorkspacePdfPreview({ pageId, pageType: "PDF", onError }),
      { initialProps: { pageId: "1" } },
    );
    await waitFor(() => expect(result.current).toMatch(/^blob:test\//));

    rerender({ pageId: "2" });
    expect(result.current).toBe("");

    secondUrl.resolve({ url: "/workspace/pages/2/pdf/content", expires_in: "900" });
    await waitFor(() => expect(getWorkspacePdfBlob).toHaveBeenCalledWith("/workspace/pages/2/pdf/content"));
    await waitFor(() => expect(result.current).toMatch(/^blob:test\//));
  });

  it("진행 중인 동일 PDF 요청을 재사용한다", async () => {
    const pdfUrl = createDeferred<{ url: string; expires_in: string }>();
    getWorkspacePdfUrl.mockReturnValue(pdfUrl.promise);
    const { result, rerender } = renderHook(
      ({ pageId, pageType }) => useWorkspacePdfPreview({ pageId, pageType, onError }),
      { initialProps: { pageId: "1" as string | null, pageType: "PDF" as const } },
    );

    rerender({ pageId: null, pageType: "MARKDOWN" });
    rerender({ pageId: "1", pageType: "PDF" });
    expect(getWorkspacePdfUrl).toHaveBeenCalledTimes(1);

    pdfUrl.resolve({ url: "/workspace/pages/1/pdf/content", expires_in: "900" });
    await waitFor(() => expect(result.current).toMatch(/^blob:test\//));
    expect(getWorkspacePdfBlob).toHaveBeenCalledTimes(1);
  });

  it("최근 PDF 세 개만 유지하고 화면 종료 시 남은 Blob URL을 해제한다", async () => {
    const { result, rerender, unmount } = renderHook(
      ({ pageId }) => useWorkspacePdfPreview({ pageId, pageType: "PDF", onError }),
      { initialProps: { pageId: "1" } },
    );
    await waitFor(() => expect(result.current).toMatch(/^blob:test\//));
    const firstUrl = result.current;

    for (const pageId of ["2", "3", "4"]) {
      rerender({ pageId });
      await waitFor(() => expect(getWorkspacePdfUrl).toHaveBeenCalledWith(pageId));
      await waitFor(() => expect(result.current).toMatch(/^blob:test\//));
    }

    expect(revokeObjectURL).toHaveBeenCalledWith(firstUrl);
    expect(revokeObjectURL).toHaveBeenCalledTimes(1);
    act(() => unmount());
    expect(revokeObjectURL).toHaveBeenCalledTimes(4);
  });
});

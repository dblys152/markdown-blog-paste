import { act, renderHook, waitFor } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import type { WorkspacePageListItem } from "../../../src/features/workspace/api";
import { useWorkspacePageMove } from "../../../src/pages/workspace/useWorkspacePageMove";

const { moveWorkspacePage } = vi.hoisted(() => ({ moveWorkspacePage: vi.fn() }));

vi.mock("../../../src/features/workspace/api", async (importOriginal) => ({
  ...await importOriginal<typeof import("../../../src/features/workspace/api")>(),
  moveWorkspacePage,
}));

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((resolvePromise) => {
    resolve = resolvePromise;
  });
  return { promise, resolve };
}

const initialPages: WorkspacePageListItem[] = [
  { id: "10", owner_id: "1", title: "A", parent_id: null, sort_order: 0 },
  { id: "20", owner_id: "1", title: "B", parent_id: null, sort_order: 1 },
  { id: "30", owner_id: "1", title: "C", parent_id: null, sort_order: 2 },
];

describe("useWorkspacePageMove", () => {
  it("연속 이동 요청을 직렬 처리하고 이전 응답을 현재 화면에 다시 적용하지 않는다", async () => {
    const firstMove = createDeferred<WorkspacePageListItem>();
    const secondMove = createDeferred<WorkspacePageListItem>();
    moveWorkspacePage
      .mockReturnValueOnce(firstMove.promise)
      .mockReturnValueOnce(secondMove.promise);

    const { result } = renderHook(() => {
      const [pages, setPages] = useState(initialPages);
      const [expandedPageIds, setExpandedPageIds] = useState(new Set<string>());
      const movePage = useWorkspacePageMove({ pages, setPages, setExpandedPageIds, onError: vi.fn() });
      return { pages, expandedPageIds, movePage };
    });

    act(() => result.current.movePage("20", { parentId: "10", sortOrder: 0 }));
    act(() => result.current.movePage("20", { parentId: null, sortOrder: 2 }));
    expect(result.current.pages.find((page) => page.id === "20")).toMatchObject({ parent_id: null, sort_order: 2 });

    await waitFor(() => expect(moveWorkspacePage).toHaveBeenCalledTimes(1));
    firstMove.resolve({ ...initialPages[1], parent_id: "10", sort_order: 0 });
    await waitFor(() => expect(moveWorkspacePage).toHaveBeenCalledTimes(2));
    expect(result.current.pages.find((page) => page.id === "20")).toMatchObject({ parent_id: null, sort_order: 2 });

    secondMove.resolve({ ...initialPages[1], parent_id: null, sort_order: 2 });
    await waitFor(() => expect(result.current.pages.find((page) => page.id === "20")).toMatchObject({ parent_id: null, sort_order: 2 }));
  });
});

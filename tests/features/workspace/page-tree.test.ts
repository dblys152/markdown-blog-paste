import { describe, expect, it } from "vitest";
import type { WorkspacePage } from "../../../src/features/workspace/api";
import {
  applyPageMove,
  resolvePageMoveDestination,
} from "../../../src/features/workspace/page-tree";

const pages: WorkspacePage[] = [
  { id: "1", owner_id: "9", title: "A", contents: "", parent_id: null, sort_order: 0 },
  { id: "2", owner_id: "9", title: "B", contents: "", parent_id: null, sort_order: 1 },
  { id: "3", owner_id: "9", title: "C", contents: "", parent_id: "1", sort_order: 0 },
];

describe("page tree move", () => {
  it("항목 가운데 드롭은 마지막 하위 위치를 계산한다", () => {
    expect(resolvePageMoveDestination(pages, "2", "1", "inside")).toEqual({
      parentId: "1",
      sortOrder: 1,
    });
  });

  it("항목 위아래 드롭은 같은 계층 순서를 계산한다", () => {
    expect(resolvePageMoveDestination(pages, "1", "2", "after")).toEqual({
      parentId: null,
      sortOrder: 1,
    });
    expect(resolvePageMoveDestination(pages, "2", "1", "before")).toEqual({
      parentId: null,
      sortOrder: 0,
    });
  });

  it("이동 후 이전 계층과 새 계층의 순서를 다시 매긴다", () => {
    const moved = applyPageMove(pages, "2", { parentId: "1", sortOrder: 0 });

    expect(moved.find((page) => page.id === "2")).toMatchObject({ parent_id: "1", sort_order: 0 });
    expect(moved.find((page) => page.id === "3")).toMatchObject({ parent_id: "1", sort_order: 1 });
    expect(moved.find((page) => page.id === "1")).toMatchObject({ parent_id: null, sort_order: 0 });
  });
});

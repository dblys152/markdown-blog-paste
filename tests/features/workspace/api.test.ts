import { beforeEach, describe, expect, it, vi } from "vitest";

const { authenticatedRequest } = vi.hoisted(() => ({ authenticatedRequest: vi.fn() }));

vi.mock("../../../src/features/auth/api", () => ({ authenticatedRequest }));

import {
  createWorkspacePage,
  deleteWorkspacePage,
  getWorkspacePage,
  listWorkspacePages,
  moveWorkspacePage,
  updateWorkspacePage,
} from "../../../src/features/workspace/api";

describe("workspace api", () => {
  beforeEach(() => authenticatedRequest.mockReset());

  it("페이지 목록을 인증 요청으로 조회한다", async () => {
    authenticatedRequest.mockResolvedValue([]);

    await listWorkspacePages();

    expect(authenticatedRequest).toHaveBeenCalledWith("/workspace/pages");
  });

  it("선택한 페이지 상세를 별도 요청으로 조회한다", async () => {
    authenticatedRequest.mockResolvedValue({ id: "10", content: "# 본문" });

    await getWorkspacePage("10");

    expect(authenticatedRequest).toHaveBeenCalledWith("/workspace/pages/10");
  });

  it("동시에 요청한 페이지 목록은 하나의 네트워크 요청을 공유한다", async () => {
    authenticatedRequest.mockResolvedValue([]);

    const first = listWorkspacePages();
    const second = listWorkspacePages();

    expect(first).toBe(second);
    await Promise.all([first, second]);
    expect(authenticatedRequest).toHaveBeenCalledTimes(1);
  });

  it("페이지 생성·수정·삭제 요청을 전달한다", async () => {
    authenticatedRequest.mockResolvedValue(undefined);

    await createWorkspacePage({ title: "새 페이지", parent_id: null });
    await updateWorkspacePage("10", { content: "# 본문" });
    await deleteWorkspacePage("10");
    await moveWorkspacePage("10", { parent_id: "20", position: 1 });

    expect(authenticatedRequest).toHaveBeenNthCalledWith(1, "/workspace/pages", {
      method: "POST",
      body: JSON.stringify({ title: "새 페이지", parent_id: null }),
    });
    expect(authenticatedRequest).toHaveBeenNthCalledWith(2, "/workspace/pages/10", {
      method: "PATCH",
      body: JSON.stringify({ content: "# 본문" }),
    });
    expect(authenticatedRequest).toHaveBeenNthCalledWith(3, "/workspace/pages/10", {
      method: "DELETE",
    });
    expect(authenticatedRequest).toHaveBeenNthCalledWith(4, "/workspace/pages/10/move", {
      method: "PATCH",
      body: JSON.stringify({ parent_id: "20", position: 1 }),
    });
  });
});

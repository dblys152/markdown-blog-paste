import { type Dispatch, type SetStateAction, useCallback, useRef } from "react";
import { moveWorkspacePage, type WorkspacePageListItem } from "../../features/workspace/api";
import { applyPageMove, type PageMoveDestination } from "../../features/workspace/page-tree";

interface UseWorkspacePageMoveOptions {
  pages: WorkspacePageListItem[];
  setPages: Dispatch<SetStateAction<WorkspacePageListItem[]>>;
  setExpandedPageIds: Dispatch<SetStateAction<Set<string>>>;
  onError: () => void;
}

export function useWorkspacePageMove({
  pages,
  setPages,
  setExpandedPageIds,
  onError,
}: UseWorkspacePageMoveOptions) {
  const requestQueue = useRef<Promise<void>>(Promise.resolve());
  const nextOperationId = useRef(0);
  const latestOperationByPage = useRef(new Map<string, number>());

  return useCallback((pageId: string, destination: PageMoveDestination) => {
    const originalPage = pages.find((page) => page.id === pageId);
    if (!originalPage) return;

    const operationId = ++nextOperationId.current;
    latestOperationByPage.current.set(pageId, operationId);
    const originalDestination = {
      parentId: originalPage.parent_id,
      sortOrder: originalPage.sort_order,
    };

    setPages((current) => applyPageMove(current, pageId, destination));
    if (destination.parentId !== null) {
      setExpandedPageIds((current) => new Set(current).add(destination.parentId as string));
    }

    const request = requestQueue.current.then(() => moveWorkspacePage(pageId, {
      parent_id: destination.parentId,
      sort_order: destination.sortOrder,
    }));
    requestQueue.current = request.then(() => undefined, () => undefined);

    void request.catch(() => {
      if (latestOperationByPage.current.get(pageId) !== operationId) return;
      setPages((current) => applyPageMove(current, pageId, originalDestination));
      onError();
    });
  }, [onError, pages, setExpandedPageIds, setPages]);
}

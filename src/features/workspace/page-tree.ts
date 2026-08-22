import type { WorkspacePageListItem } from "./api";

export type DropPlacement = "before" | "inside" | "after";

export type PageMoveDestination = {
  parentId: string | null;
  sortOrder: number;
};

function sortedSiblings(pages: WorkspacePageListItem[], parentId: string | null, excludedId: string) {
  return pages
    .filter((page) => page.parent_id === parentId && page.id !== excludedId)
    .sort((left, right) => left.sort_order - right.sort_order || left.id.localeCompare(right.id));
}

export function resolvePageMoveDestination(
  pages: WorkspacePageListItem[],
  draggedId: string,
  targetId: string,
  placement: DropPlacement,
): PageMoveDestination | null {
  const target = pages.find((page) => page.id === targetId);
  if (!target || draggedId === targetId) return null;

  if (placement === "inside") {
    return {
      parentId: target.id,
      sortOrder: sortedSiblings(pages, target.id, draggedId).length,
    };
  }

  const siblings = sortedSiblings(pages, target.parent_id, draggedId);
  const targetIndex = siblings.findIndex((page) => page.id === target.id);
  if (targetIndex < 0) return null;
  return {
    parentId: target.parent_id,
    sortOrder: targetIndex + (placement === "after" ? 1 : 0),
  };
}

export function applyPageMove(
  pages: WorkspacePageListItem[],
  pageId: string,
  destination: PageMoveDestination,
): WorkspacePageListItem[] {
  const movingPage = pages.find((page) => page.id === pageId);
  if (!movingPage) return pages;

  const oldParentId = movingPage.parent_id;
  const withoutMoving = pages.filter((page) => page.id !== pageId);
  const oldSiblings = sortedSiblings(withoutMoving, oldParentId, pageId);
  const targetSiblings = oldParentId === destination.parentId
    ? oldSiblings
    : sortedSiblings(withoutMoving, destination.parentId, pageId);
  const targetPosition = Math.min(destination.sortOrder, targetSiblings.length);
  const movedPage = { ...movingPage, parent_id: destination.parentId, sort_order: targetPosition };
  targetSiblings.splice(targetPosition, 0, movedPage);

  const reordered = new Map<string, WorkspacePageListItem>();
  if (oldParentId !== destination.parentId) {
    oldSiblings.forEach((page, index) => reordered.set(page.id, { ...page, sort_order: index }));
  }
  targetSiblings.forEach((page, index) => reordered.set(page.id, {
    ...page,
    parent_id: destination.parentId,
    sort_order: index,
  }));

  return pages.map((page) => reordered.get(page.id) ?? page);
}

import { authenticatedRequest } from "../auth/api";

export type WorkspacePageListItem = {
  id: string;
  owner_id: string;
  title: string;
  parent_id: string | null;
  sort_order: number;
};

export type WorkspacePage = WorkspacePageListItem & {
  contents: string;
};

export type TrashedWorkspacePage = {
  id: string;
  parent_id: string | null;
  title: string;
  sort_order: number;
  deleted_at: string;
  expires_at: string;
};

export type CreateWorkspacePageInput = {
  title: string;
  content?: string;
  parent_id?: string | null;
};

export type UpdateWorkspacePageInput = {
  title?: string;
  content?: string;
};

export type MoveWorkspacePageInput = {
  parent_id: string | null;
  sort_order: number;
};

let listPagesPromise: Promise<WorkspacePageListItem[]> | null = null;

export function listWorkspacePages(): Promise<WorkspacePageListItem[]> {
  if (!listPagesPromise) {
    listPagesPromise = authenticatedRequest<WorkspacePageListItem[]>("/workspace/pages")
      .finally(() => {
        listPagesPromise = null;
      });
  }
  return listPagesPromise;
}

export function searchWorkspacePages(query: string): Promise<WorkspacePageListItem[]> {
  const params = new URLSearchParams({ q: query });
  return authenticatedRequest<WorkspacePageListItem[]>(`/workspace/pages/search?${params}`);
}

export function getWorkspacePage(pageId: string): Promise<WorkspacePage> {
  return authenticatedRequest<WorkspacePage>(`/workspace/pages/${pageId}`);
}

export function createWorkspacePage(input: CreateWorkspacePageInput): Promise<WorkspacePage> {
  return authenticatedRequest<WorkspacePage>("/workspace/pages", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateWorkspacePage(
  pageId: string,
  input: UpdateWorkspacePageInput,
): Promise<WorkspacePage> {
  return authenticatedRequest<WorkspacePage>(`/workspace/pages/${pageId}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function deleteWorkspacePage(pageId: string): Promise<void> {
  return authenticatedRequest<void>(`/workspace/pages/${pageId}`, { method: "DELETE" });
}

export function moveWorkspacePage(
  pageId: string,
  input: MoveWorkspacePageInput,
): Promise<WorkspacePage> {
  return authenticatedRequest<WorkspacePage>(`/workspace/pages/${pageId}/move`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function listTrashedWorkspacePages(): Promise<TrashedWorkspacePage[]> {
  return authenticatedRequest<TrashedWorkspacePage[]>("/workspace/trash");
}

export function getTrashedWorkspacePage(pageId: string): Promise<WorkspacePage> {
  return authenticatedRequest<WorkspacePage>(`/workspace/trash/${pageId}`);
}

export function restoreWorkspacePage(pageId: string): Promise<void> {
  return authenticatedRequest<void>(`/workspace/trash/${pageId}/restore`, {
    method: "POST",
  });
}

export function permanentlyDeleteWorkspacePage(pageId: string): Promise<void> {
  return authenticatedRequest<void>(`/workspace/trash/${pageId}`, {
    method: "DELETE",
  });
}

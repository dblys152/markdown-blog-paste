import { authenticatedRequest } from "../auth/api";

export type WorkspacePage = {
  id: string;
  title: string;
  content: string;
  parent_id: string | null;
  position: number;
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

export function listWorkspacePages(): Promise<WorkspacePage[]> {
  return authenticatedRequest<WorkspacePage[]>("/workspace/pages");
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

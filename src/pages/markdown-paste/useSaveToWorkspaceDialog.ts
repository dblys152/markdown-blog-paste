import { useState } from "react";
import {
  createWorkspacePage,
  getWorkspacePage,
  listWorkspacePages,
  updateWorkspacePage,
  type WorkspacePageListItem,
} from "../../features/workspace/api";
import { loadGuestDraft, saveGuestDraft, type GuestDraft } from "../workspace/guest-draft-store";

export type SaveMode = "replace" | "append";
export type SaveTargetLoadStatus = "idle" | "loading" | "ready" | "error";
type AuthStatus = "loading" | "guest" | "authenticated";

interface UseSaveToWorkspaceDialogOptions {
  authStatus: AuthStatus;
  markdown: string;
  title: string;
  onMessage: (message: string) => void;
  onSaved: (pageId?: string) => void;
}

export interface SaveToWorkspaceDialogController {
  isOpen: boolean;
  isAuthenticated: boolean;
  isSaving: boolean;
  saveMode: SaveMode;
  setSaveMode: (mode: SaveMode) => void;
  guestDraft: GuestDraft | null;
  guestDraftStatus: SaveTargetLoadStatus;
  workspacePages: WorkspacePageListItem[];
  workspacePagesStatus: SaveTargetLoadStatus;
  workspaceSaveTarget: string;
  setWorkspaceSaveTarget: (target: string) => void;
  open: () => void;
  close: () => void;
  retryGuestDraft: () => void;
  retryWorkspacePages: () => void;
  confirm: () => void;
}

export function useSaveToWorkspaceDialog({
  authStatus,
  markdown,
  title,
  onMessage,
  onSaved,
}: UseSaveToWorkspaceDialogOptions): SaveToWorkspaceDialogController {
  const isAuthenticated = authStatus === "authenticated";
  const [isOpen, setIsOpen] = useState(false);
  const [saveMode, setSaveMode] = useState<SaveMode>("replace");
  const [guestDraft, setGuestDraft] = useState<GuestDraft | null>(null);
  const [guestDraftStatus, setGuestDraftStatus] = useState<SaveTargetLoadStatus>("idle");
  const [workspacePages, setWorkspacePages] = useState<WorkspacePageListItem[]>([]);
  const [workspacePagesStatus, setWorkspacePagesStatus] = useState<SaveTargetLoadStatus>("idle");
  const [workspaceSaveTarget, setWorkspaceSaveTarget] = useState("new");
  const [isSaving, setIsSaving] = useState(false);

  const loadWorkspaceSaveTargets = async () => {
    setWorkspacePagesStatus("loading");
    try {
      setWorkspacePages(await listWorkspacePages());
      setWorkspacePagesStatus("ready");
    } catch {
      setWorkspacePagesStatus("error");
    }
  };

  const loadGuestSaveTarget = async () => {
    setGuestDraftStatus("loading");
    try {
      setGuestDraft(await loadGuestDraft());
      setGuestDraftStatus("ready");
    } catch {
      setGuestDraftStatus("error");
    }
  };

  const open = () => {
    if (authStatus === "loading") {
      onMessage("로그인 상태를 확인하고 있습니다. 잠시 후 다시 시도해 주세요.");
      return;
    }
    setSaveMode("replace");
    setWorkspaceSaveTarget("new");
    setIsOpen(true);
    if (isAuthenticated) {
      if (workspacePagesStatus === "idle" || workspacePagesStatus === "error") void loadWorkspaceSaveTargets();
      return;
    }
    if (guestDraftStatus === "idle" || guestDraftStatus === "error") void loadGuestSaveTarget();
  };

  const close = () => {
    if (!isSaving) setIsOpen(false);
  };

  const confirm = async () => {
    const isReady = isAuthenticated
      ? workspacePagesStatus === "ready"
      : guestDraftStatus === "ready";
    if (!isReady || isSaving) return;

    setIsSaving(true);
    try {
      if (isAuthenticated) {
        let savedPageId: string;
        if (workspaceSaveTarget === "new") {
          const createdPage = await createWorkspacePage({ title, content: markdown, parent_id: null });
          savedPageId = createdPage.id;
        } else {
          const targetPage = workspacePages.find((page) => page.id === workspaceSaveTarget);
          if (!targetPage) throw new Error("저장 대상을 찾을 수 없습니다.");
          const existingMarkdown = saveMode === "append"
            ? ((await getWorkspacePage(targetPage.id)).contents ?? "").trimEnd()
            : "";
          const nextMarkdown = saveMode === "append" && existingMarkdown
            ? `${existingMarkdown}\n\n${markdown}`
            : markdown;
          await updateWorkspacePage(targetPage.id, { content: nextMarkdown });
          savedPageId = targetPage.id;
        }
        setIsOpen(false);
        onSaved(savedPageId);
        return;
      }

      const existingMarkdown = guestDraft?.markdown.trimEnd() ?? "";
      const nextMarkdown = saveMode === "append" && existingMarkdown
        ? `${existingMarkdown}\n\n${markdown}`
        : markdown;
      await saveGuestDraft({ title: "임시 페이지", markdown: nextMarkdown, updatedAt: Date.now() });
      setIsOpen(false);
      onSaved();
    } catch {
      onMessage("기록장에 저장할 수 없습니다.");
    } finally {
      setIsSaving(false);
    }
  };

  return {
    isOpen,
    isAuthenticated,
    isSaving,
    saveMode,
    setSaveMode,
    guestDraft,
    guestDraftStatus,
    workspacePages,
    workspacePagesStatus,
    workspaceSaveTarget,
    setWorkspaceSaveTarget,
    open,
    close,
    retryGuestDraft: () => void loadGuestSaveTarget(),
    retryWorkspacePages: () => void loadWorkspaceSaveTargets(),
    confirm: () => void confirm(),
  };
}

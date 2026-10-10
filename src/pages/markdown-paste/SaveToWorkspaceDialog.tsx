import { useEffect } from "react";
import { WorkspaceSaveTargetPicker } from "./WorkspaceSaveTargetPicker";
import type { SaveToWorkspaceDialogController } from "./useSaveToWorkspaceDialog";

export function SaveToWorkspaceDialog({ controller }: { controller: SaveToWorkspaceDialogController }) {
  const {
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
    close,
    retryGuestDraft,
    retryWorkspacePages,
    confirm,
  } = controller;

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, close]);

  if (!isOpen) return null;

  const isReady = isAuthenticated
    ? workspacePagesStatus === "ready"
    : guestDraftStatus === "ready";

  return (
    <div
      className="save-dialog-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) close();
      }}
    >
      <section className={`save-dialog${isAuthenticated ? " has-workspace-picker" : ""}`} role="dialog" aria-modal="true" aria-labelledby="save-dialog-title">
        <div className="save-dialog-heading">
          <h2 id="save-dialog-title">기록장에 저장</h2>
          <button type="button" aria-label="닫기" onClick={close} disabled={isSaving}>×</button>
        </div>
        {isAuthenticated ? (
          <>
            <span className="save-dialog-select-label">저장 대상</span>
            {workspacePagesStatus === "loading" ? (
              <div className="workspace-save-picker-status" role="status">페이지 목록을 불러오는 중…</div>
            ) : workspacePagesStatus === "error" ? (
              <LoadError message="페이지 목록을 불러오지 못했습니다." onRetry={retryWorkspacePages} />
            ) : (
              <WorkspaceSaveTargetPicker pages={workspacePages} value={workspaceSaveTarget} onChange={setWorkspaceSaveTarget} />
            )}
          </>
        ) : guestDraftStatus === "loading" ? (
          <div className="workspace-save-picker-status" role="status">임시 페이지 정보를 불러오는 중…</div>
        ) : guestDraftStatus === "error" ? (
          <LoadError message="임시 페이지 정보를 불러오지 못했습니다." onRetry={retryGuestDraft} />
        ) : <p>비회원은 임시 페이지 한 개만 사용할 수 있습니다.</p>}
        {((!isAuthenticated && guestDraftStatus === "ready") || (isAuthenticated && workspaceSaveTarget !== "new")) && (
          <fieldset>
            <label>
              <input type="radio" name="save-mode" checked={saveMode === "replace"} onChange={() => setSaveMode("replace")} />
              <span>{isAuthenticated ? "선택한 페이지를 현재 내용으로 교체" : "임시 페이지를 현재 내용으로 교체"}</span>
            </label>
            {!isAuthenticated && saveMode === "replace" && guestDraft?.markdown.trim() && (
              <small>기존 임시 페이지 내용이 현재 내용으로 교체됩니다.</small>
            )}
            <label>
              <input type="radio" name="save-mode" checked={saveMode === "append"} onChange={() => setSaveMode("append")} />
              <span>{isAuthenticated ? "선택한 페이지에 내용 추가" : "임시 페이지에 내용 추가"}</span>
            </label>
          </fieldset>
        )}
        <div className="save-dialog-actions">
          <button type="button" onClick={close} disabled={isSaving}>취소</button>
          <button type="button" className="is-primary" onClick={confirm} disabled={isSaving || !isReady}>
            {isSaving ? "저장 중…" : (isAuthenticated ? "저장" : "임시 페이지에 저장")}
          </button>
        </div>
      </section>
    </div>
  );
}

function LoadError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="workspace-save-picker-status is-error" role="alert">
      <span>{message}</span>
      <button type="button" onClick={onRetry}>다시 시도</button>
    </div>
  );
}

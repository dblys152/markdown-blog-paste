import { type CSSProperties, type DragEvent, type KeyboardEvent, type PointerEvent, type ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../features/auth/AuthProvider";
import {
  createWorkspacePage,
  deleteWorkspacePage,
  listWorkspacePages,
  moveWorkspacePage,
  updateWorkspacePage,
  type WorkspacePage,
} from "../../features/workspace/api";
import {
  applyPageMove,
  resolvePageMoveDestination,
  type DropPlacement,
} from "../../features/workspace/page-tree";
import { convertMarkdown } from "../../shared/markdown/converter-core";
import type { ConversionResult } from "../../shared/markdown/types";
import { DocumentActions } from "../../shared/ui/DocumentActions";
import { loadGuestDraft, saveGuestDraft } from "./guest-draft-store";

const SAMPLE_MARKDOWN = `# 임시 Markdown 페이지

로그인 없이 자유롭게 작성해보세요. 이 내용은 현재 브라우저에 자동으로 저장됩니다.

## 시작하기

- Markdown 문법으로 내용을 작성할 수 있습니다.
- 오른쪽에서 변환 결과를 바로 확인할 수 있습니다.
- 로그인하면 이 페이지를 내 기록장으로 옮길 수 있습니다.

## Mermaid 미리보기

\`\`\`mermaid
flowchart LR
    A[Markdown 작성] --> B[실시간 미리보기]
    B --> C[로그인]
    C --> D[내 기록장으로 이전]
\`\`\`
`;

const DEFAULT_EDITOR_RATIO = 0.48;
const MIN_EDITOR_WIDTH = 360;
const MIN_PREVIEW_WIDTH = 460;
const DIVIDER_WIDTH = 14;
const EDITOR_RATIO_STORAGE_KEY = "md2blog-workspace-editor-ratio";

function loadEditorRatio(): number {
  try {
    const storedRatio = Number(window.localStorage.getItem(EDITOR_RATIO_STORAGE_KEY));
    return Number.isFinite(storedRatio) && storedRatio > 0 && storedRatio < 1 ? storedRatio : DEFAULT_EDITOR_RATIO;
  } catch {
    return DEFAULT_EDITOR_RATIO;
  }
}

function saveEditorRatio(ratio: number): void {
  try {
    window.localStorage.setItem(EDITOR_RATIO_STORAGE_KEY, String(ratio));
  } catch {
    // 저장소 접근이 제한되어도 현재 세션의 리사이즈 기능은 유지합니다.
  }
}

export function WorkspaceGatePage() {
  const { status: authStatus } = useAuth();
  const isAuthenticated = authStatus === "authenticated";
  const [pages, setPages] = useState<WorkspacePage[]>([]);
  const [selectedPageId, setSelectedPageId] = useState<string | null>(null);
  const [draggedPageId, setDraggedPageId] = useState<string | null>(null);
  const [dropHint, setDropHint] = useState<{ pageId: string; placement: DropPlacement } | null>(null);
  const [openPageMenuId, setOpenPageMenuId] = useState<string | null>(null);
  const [openPageMenuUpward, setOpenPageMenuUpward] = useState(false);
  const [renamingPageId, setRenamingPageId] = useState<string | null>(null);
  const [renameTitle, setRenameTitle] = useState("");
  const [markdown, setMarkdown] = useState(SAMPLE_MARKDOWN);
  const [result, setResult] = useState<ConversionResult | null>(null);
  const [isConverting, setIsConverting] = useState(true);
  const [toast, setToast] = useState("");
  const [saveState, setSaveState] = useState<"loading" | "saving" | "saved" | "error">("loading");
  const [isGuestInfoOpen, setIsGuestInfoOpen] = useState(true);
  const [workspaceLoadState, setWorkspaceLoadState] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [workspaceReloadKey, setWorkspaceReloadKey] = useState(0);
  const [editorRatio, setEditorRatio] = useState(loadEditorRatio);
  const [editorWidth, setEditorWidth] = useState<number | null>(null);
  const [isResizing, setIsResizing] = useState(false);
  const [mobilePane, setMobilePane] = useState<"pages" | "editor" | "preview">("pages");
  const workspaceRef = useRef<HTMLElement>(null);
  const resizingRef = useRef(false);
  const hydrated = useRef(false);
  const serverHydrated = useRef(false);
  const skipNextServerSave = useRef(false);
  const toastTimer = useRef<number | undefined>(undefined);
  const selectedPage = pages.find((page) => page.id === selectedPageId) ?? null;
  const title = isAuthenticated ? (selectedPage?.title ?? "페이지를 선택하세요") : "임시 페이지";

  const showToast = useCallback((message: string) => {
    window.clearTimeout(toastTimer.current);
    setToast(message);
    toastTimer.current = window.setTimeout(() => setToast(""), 2600);
  }, []);

  useEffect(() => () => window.clearTimeout(toastTimer.current), []);

  useEffect(() => {
    if (authStatus !== "guest") return;
    loadGuestDraft()
      .then(async (draft) => {
        if (draft?.markdown) setMarkdown(draft.markdown);
        if (draft && draft.title !== title) {
          await saveGuestDraft({ ...draft, title, updatedAt: Date.now() });
        }
      })
      .catch(() => setSaveState("error"))
      .finally(() => {
        hydrated.current = true;
        setSaveState((current) => (current === "error" ? current : "saved"));
      });
  }, [authStatus]);

  useEffect(() => {
    if (!isAuthenticated) {
      serverHydrated.current = false;
      setWorkspaceLoadState("idle");
      return;
    }
    let cancelled = false;
    serverHydrated.current = false;
    setWorkspaceLoadState("loading");
    setSaveState("loading");
    listWorkspacePages()
      .then((loadedPages) => {
        if (cancelled) return;
        setPages(loadedPages);
        const firstPage = loadedPages[0] ?? null;
        setSelectedPageId(firstPage?.id ?? null);
        setMarkdown(firstPage?.content ?? "");
        skipNextServerSave.current = true;
        serverHydrated.current = true;
        setWorkspaceLoadState("ready");
        setSaveState("saved");
      })
      .catch(() => {
        if (!cancelled) {
          setWorkspaceLoadState("error");
          setSaveState("error");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, workspaceReloadKey]);

  useEffect(() => {
    let cancelled = false;
    setIsConverting(true);
    convertMarkdown(markdown, "basic", title, undefined, (partialResult) => {
      if (!cancelled) setResult(partialResult);
    }).then((result) => {
      if (cancelled) return;
      setResult(result);
      setIsConverting(false);
    });
    return () => {
      cancelled = true;
    };
  }, [markdown, title]);

  useEffect(() => {
    if (authStatus !== "guest" || !hydrated.current) return;
    setSaveState("saving");
    const timer = window.setTimeout(() => {
      saveGuestDraft({ title, markdown, updatedAt: Date.now() })
        .then(() => setSaveState("saved"))
        .catch(() => setSaveState("error"));
    }, 450);
    return () => window.clearTimeout(timer);
  }, [authStatus, markdown, title]);

  useEffect(() => {
    if (!isAuthenticated || !serverHydrated.current || !selectedPageId) return;
    if (skipNextServerSave.current) {
      skipNextServerSave.current = false;
      return;
    }
    if (!title.trim()) {
      setSaveState("error");
      return;
    }
    setSaveState("saving");
    const timer = window.setTimeout(() => {
      updateWorkspacePage(selectedPageId, { title, content: markdown })
        .then((updatedPage) => {
          setPages((current) => current.map((page) => page.id === updatedPage.id ? updatedPage : page));
          setSaveState("saved");
        })
        .catch(() => setSaveState("error"));
    }, 600);
    return () => window.clearTimeout(timer);
  }, [isAuthenticated, markdown, selectedPageId, title]);

  const selectPage = useCallback((page: WorkspacePage) => {
    setOpenPageMenuId(null);
    skipNextServerSave.current = true;
    setSelectedPageId(page.id);
    setMarkdown(page.content);
    setSaveState("saved");
    setMobilePane("editor");
  }, []);

  const addPage = useCallback(async (parentId: string | null = null) => {
    try {
      const created = await createWorkspacePage({
        title: "새 페이지",
        content: "# 새 페이지\n",
        parent_id: parentId,
      });
      setPages((current) => [...current, created]);
      selectPage(created);
    } catch {
      showToast("페이지를 만들지 못했습니다.");
    }
  }, [selectPage, showToast]);

  const removePage = useCallback(async (page: WorkspacePage) => {
    const hasChildren = pages.some((candidate) => candidate.parent_id === page.id);
    const confirmationMessage = hasChildren
      ? `'${page.title}' 페이지와 모든 하위 페이지를 삭제할까요?`
      : `'${page.title}' 페이지를 삭제할까요?`;
    if (!window.confirm(confirmationMessage)) return;
    try {
      await deleteWorkspacePage(page.id);
      const deletedIds = new Set([page.id]);
      let changed = true;
      while (changed) {
        changed = false;
        for (const candidate of pages) {
          if (candidate.parent_id && deletedIds.has(candidate.parent_id) && !deletedIds.has(candidate.id)) {
            deletedIds.add(candidate.id);
            changed = true;
          }
        }
      }
      const remaining = pages.filter((candidate) => !deletedIds.has(candidate.id));
      setPages(remaining);
      if (deletedIds.has(selectedPageId ?? "")) {
        const nextPage = remaining[0] ?? null;
        setSelectedPageId(nextPage?.id ?? null);
        setMarkdown(nextPage?.content ?? "");
        skipNextServerSave.current = true;
      }
    } catch {
      showToast("페이지를 삭제하지 못했습니다.");
    }
  }, [pages, selectedPageId, showToast]);

  const beginRenamePage = (page: WorkspacePage) => {
    setOpenPageMenuId(null);
    setRenamingPageId(page.id);
    setRenameTitle(page.title);
  };

  const commitPageRename = async (page: WorkspacePage) => {
    const nextTitle = renameTitle.trim();
    setRenamingPageId(null);
    if (!nextTitle || nextTitle === page.title) return;
    try {
      const updated = await updateWorkspacePage(page.id, { title: nextTitle });
      if (page.id === selectedPageId) skipNextServerSave.current = true;
      setPages((current) => current.map((candidate) => (
        candidate.id === updated.id ? updated : candidate
      )));
    } catch {
      showToast("페이지 이름을 변경하지 못했습니다.");
    }
  };

  const getDropPlacement = (event: DragEvent<HTMLDivElement>): DropPlacement => {
    const rect = event.currentTarget.getBoundingClientRect();
    const ratio = rect.height > 0 ? (event.clientY - rect.top) / rect.height : 0.5;
    if (ratio < 0.25) return "before";
    if (ratio > 0.75) return "after";
    return "inside";
  };

  const handlePageDrop = async (
    event: DragEvent<HTMLDivElement>,
    targetPage: WorkspacePage,
  ) => {
    event.preventDefault();
    event.stopPropagation();
    const placement = getDropPlacement(event);
    const destination = draggedPageId
      ? resolvePageMoveDestination(pages, draggedPageId, targetPage.id, placement)
      : null;
    setDropHint(null);
    setDraggedPageId(null);
    if (!draggedPageId || !destination) return;

    try {
      const moved = await moveWorkspacePage(draggedPageId, {
        parent_id: destination.parentId,
        position: destination.position,
      });
      setPages((current) => applyPageMove(current, moved.id, {
        parentId: moved.parent_id,
        position: moved.position,
      }));
    } catch {
      showToast("페이지를 이동하지 못했습니다.");
    }
  };

  const renderPageTree = (parentId: string | null, depth = 0): ReactNode => {
    return pages
      .filter((page) => page.parent_id === parentId)
      .sort((left, right) => left.position - right.position)
      .map((page) => (
        <div key={page.id} className="workspace-page-node">
          <div
            className={`workspace-page-item ${page.id === selectedPageId ? "is-active" : ""} ${draggedPageId === page.id ? "is-dragging" : ""} ${dropHint?.pageId === page.id ? `drop-${dropHint.placement}` : ""}`}
            style={{ paddingLeft: `${16 + Math.min(depth, 6) * 16}px` }}
            draggable
            onDragStart={(event) => {
              setOpenPageMenuId(null);
              event.dataTransfer.effectAllowed = "move";
              event.dataTransfer.setData("text/plain", page.id);
              setDraggedPageId(page.id);
            }}
            onDragEnd={() => {
              setDraggedPageId(null);
              setDropHint(null);
            }}
            onDragOver={(event) => {
              if (!draggedPageId || draggedPageId === page.id) return;
              event.preventDefault();
              event.stopPropagation();
              event.dataTransfer.dropEffect = "move";
              setDropHint({ pageId: page.id, placement: getDropPlacement(event) });
            }}
            onDragLeave={(event) => {
              if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDropHint(null);
            }}
            onDrop={(event) => void handlePageDrop(event, page)}
          >
            {renamingPageId === page.id ? (
              <input
                className="workspace-page-rename-input"
                aria-label={`${page.title} 이름 변경`}
                value={renameTitle}
                maxLength={200}
                autoFocus
                onChange={(event) => setRenameTitle(event.target.value)}
                onBlur={() => void commitPageRename(page)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") event.currentTarget.blur();
                }}
              />
            ) : (
              <button
                type="button"
                className="workspace-page-select"
                onClick={() => selectPage(page)}
              >
                <span aria-hidden="true">▤</span><span>{page.title}</span>
              </button>
            )}
            <div className="workspace-page-actions">
              <button
                type="button"
                className="workspace-page-add-button"
                aria-label={`${page.title} 하위 페이지 추가`}
                data-tooltip="하위 페이지 추가"
                onClick={() => void addPage(page.id)}
              >+</button>
              <button
                type="button"
                aria-label={`${page.title} 메뉴`}
                onClick={(event) => {
                  if (openPageMenuId === page.id) {
                    setOpenPageMenuId(null);
                    return;
                  }

                  const list = event.currentTarget.closest<HTMLElement>(".workspace-page-list");
                  const buttonRect = event.currentTarget.getBoundingClientRect();
                  const listRect = list?.getBoundingClientRect();
                  const spaceBelow = listRect ? listRect.bottom - buttonRect.bottom : window.innerHeight - buttonRect.bottom;
                  const spaceAbove = listRect ? buttonRect.top - listRect.top : buttonRect.top;
                  setOpenPageMenuUpward(spaceBelow < 78 && spaceAbove > spaceBelow);
                  setOpenPageMenuId(page.id);
                }}
              >⋮</button>
              {openPageMenuId === page.id && (
                <div className={`workspace-page-menu ${openPageMenuUpward ? "is-upward" : ""}`} role="menu">
                  <button type="button" role="menuitem" onClick={() => beginRenamePage(page)}>이름 변경</button>
                  <button type="button" role="menuitem" className="is-danger" onClick={() => {
                    setOpenPageMenuId(null);
                    void removePage(page);
                  }}>삭제</button>
                </div>
              )}
            </div>
          </div>
          {renderPageTree(page.id, depth + 1)}
        </div>
      ));
  };

  const lineCount = useMemo(() => markdown.split("\n").length, [markdown]);

  const updateEditorRatio = useCallback((clientX: number) => {
    const workspace = workspaceRef.current;
    const editor = workspace?.querySelector<HTMLElement>(".workspace-editor");
    if (!workspace || !editor) return;

    const workspaceRect = workspace.getBoundingClientRect();
    const editorLeft = editor.getBoundingClientRect().left;
    const availableWidth = workspaceRect.right - editorLeft - DIVIDER_WIDTH;
    if (availableWidth <= MIN_EDITOR_WIDTH + MIN_PREVIEW_WIDTH) return;

    const editorWidth = Math.min(
      Math.max(clientX - editorLeft, MIN_EDITOR_WIDTH),
      availableWidth - MIN_PREVIEW_WIDTH,
    );
    setEditorWidth(editorWidth);
    setEditorRatio(editorWidth / availableWidth);
  }, []);

  const applyEditorRatio = useCallback((ratio: number) => {
    const workspace = workspaceRef.current;
    const editor = workspace?.querySelector<HTMLElement>(".workspace-editor");
    if (!workspace || !editor) return;

    const workspaceRect = workspace.getBoundingClientRect();
    const editorLeft = editor.getBoundingClientRect().left;
    const availableWidth = workspaceRect.right - editorLeft - DIVIDER_WIDTH;
    if (availableWidth <= MIN_EDITOR_WIDTH + MIN_PREVIEW_WIDTH) return;

    const nextWidth = Math.min(
      Math.max(availableWidth * ratio, MIN_EDITOR_WIDTH),
      availableWidth - MIN_PREVIEW_WIDTH,
    );
    setEditorWidth(nextWidth);
    setEditorRatio(nextWidth / availableWidth);
  }, []);

  useEffect(() => {
    saveEditorRatio(editorRatio);
  }, [editorRatio]);

  const stopDividerResize = useCallback(() => {
    resizingRef.current = false;
    setIsResizing(false);
    window.removeEventListener("pointerup", stopDividerResize);
    window.removeEventListener("pointercancel", stopDividerResize);
    window.removeEventListener("blur", stopDividerResize);
  }, []);

  const handleDividerPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.currentTarget.focus({ preventScroll: true });
    event.currentTarget.setPointerCapture(event.pointerId);
    resizingRef.current = true;
    setIsResizing(true);
    window.addEventListener("pointerup", stopDividerResize, { once: true });
    window.addEventListener("pointercancel", stopDividerResize, { once: true });
    window.addEventListener("blur", stopDividerResize, { once: true });
    updateEditorRatio(event.clientX);
  };

  const handleDividerPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    if (!resizingRef.current) return;
    updateEditorRatio(event.clientX);
  };

  const finishDividerResize = (event: PointerEvent<HTMLDivElement>) => {
    stopDividerResize();
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  };

  const handleDividerKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    const direction = event.key === "ArrowLeft" ? -1 : 1;
    applyEditorRatio(Math.min(.72, Math.max(.28, editorRatio + direction * .02)));
  };

  const workspaceStyle = {
    "--workspace-editor-size": editorWidth === null ? `${editorRatio}fr` : `${editorWidth}px`,
  } as CSSProperties;

  if (authStatus === "loading" || (isAuthenticated && workspaceLoadState !== "ready" && workspaceLoadState !== "error")) {
    return (
      <main className="workspace-loading-state" aria-live="polite" aria-busy="true">
        <span className="workspace-loading-spinner" aria-hidden="true" />
        <strong>내 기록장을 불러오는 중…</strong>
      </main>
    );
  }

  if (isAuthenticated && workspaceLoadState === "error") {
    return (
      <main className="workspace-loading-state" role="alert">
        <strong>내 기록장을 불러오지 못했습니다.</strong>
        <button type="button" onClick={() => setWorkspaceReloadKey((key) => key + 1)}>다시 시도</button>
      </main>
    );
  }

  return (
    <main ref={workspaceRef} className={`workspace-shell mobile-pane-${mobilePane} ${isResizing ? "is-resizing" : ""}`} style={workspaceStyle}>
      <div className="workspace-mobile-tabs" role="tablist" aria-label="기록장 화면">
        <button type="button" role="tab" aria-selected={mobilePane === "pages"} onClick={() => setMobilePane("pages")}>페이지</button>
        <button type="button" role="tab" aria-selected={mobilePane === "editor"} onClick={() => setMobilePane("editor")}>Markdown</button>
        <button type="button" role="tab" aria-selected={mobilePane === "preview"} onClick={() => setMobilePane("preview")}>미리보기</button>
      </div>
      <aside className="workspace-sidebar" aria-label="기록장 페이지">
        <div className="workspace-sidebar-title">
          <strong>내 기록장</strong>
        </div>

        <div className="workspace-pages-heading">
          <span>페이지</span>
          {isAuthenticated ? (
            <button
              type="button"
              className="workspace-root-page-add"
              aria-label="새 페이지 추가"
              data-tooltip="페이지 추가"
              onClick={() => void addPage()}
            >+</button>
          ) : (
            <Link
              to="/login"
              className="workspace-root-page-add"
              aria-label="새 페이지 추가"
              data-tooltip="페이지 추가"
              onClick={(event) => {
                const shouldMove = window.confirm(
                  "페이지를 추가하려면 로그인이 필요합니다.\n로그인 화면으로 이동하시겠습니까?",
                );
                if (!shouldMove) event.preventDefault();
              }}
            >+</Link>
          )}
        </div>

        {isAuthenticated ? (
          <div className="workspace-page-list" role="region" aria-label="페이지 목록">
            {pages.length > 0 ? renderPageTree(null) : (
              <p className="workspace-empty-pages">아직 페이지가 없습니다.<br />+ 버튼으로 첫 페이지를 만들어보세요.</p>
            )}
          </div>
        ) : (
          <button className="workspace-page-item is-active" type="button" onClick={() => setMobilePane("editor")}>
            <span aria-hidden="true">▤</span>
            <span>{title}</span>
          </button>
        )}

        {!isAuthenticated && isGuestInfoOpen && (
          <section className="workspace-guest-card" aria-label="임시 페이지 안내">
            <button type="button" aria-label="안내 닫기" onClick={() => setIsGuestInfoOpen(false)}>×</button>
            <strong>현재 브라우저에 저장 중</strong>
            <p>지금은 임시 페이지에 저장됩니다. 로그인하고 내 페이지에서 관리해 보세요.</p>
            <Link to="/login">내 기록장으로 옮기기</Link>
          </section>
        )}

        {!isAuthenticated && <div className="workspace-sidebar-footer">
          <span aria-hidden="true">ⓘ</span>
          브라우저 데이터를 삭제하면 임시 페이지도 사라집니다.
        </div>}
      </aside>

      <section className="workspace-editor" aria-label="Markdown 편집기">
        <div className="workspace-editor-heading">
          <div><span aria-hidden="true">✎</span><strong>Markdown</strong></div>
          <div className="workspace-document-state">
            {isAuthenticated && selectedPage ? (
              <input
                className="workspace-document-title-input"
                aria-label="페이지 제목"
                value={selectedPage.title}
                maxLength={200}
                onChange={(event) => setPages((current) => current.map((page) => (
                  page.id === selectedPage.id ? { ...page, title: event.target.value } : page
                )))}
              />
            ) : <span className="workspace-document-title">{title}</span>}
            <span aria-hidden="true">·</span>
            <span className={`workspace-save-label save-${saveState}`}>
              {saveState === "loading" && "불러오는 중"}
              {saveState === "saving" && "저장 중…"}
              {saveState === "saved" && (isAuthenticated ? "✓ 저장됨" : "✓ 브라우저에 저장됨")}
              {saveState === "error" && "저장 실패"}
            </span>
          </div>
        </div>
        <div className="workspace-code-area">
          <div className="workspace-line-numbers" aria-hidden="true">
            {Array.from({ length: Math.max(lineCount, 32) }, (_, index) => <span key={index}>{index + 1}</span>)}
          </div>
          <textarea
            aria-label="Markdown 내용"
            spellCheck={false}
            value={markdown}
            onChange={(event) => setMarkdown(event.target.value)}
            disabled={isAuthenticated && !selectedPage}
          />
        </div>
        <footer className="workspace-statusbar">
          <span>줄 1, 열 1</span><span>Markdown</span><span>{markdown.length.toLocaleString("ko-KR")}자</span>
        </footer>
      </section>

      <div
        className="workspace-divider"
        role="separator"
        aria-label="에디터와 미리보기 너비 조절"
        aria-orientation="vertical"
        aria-valuemin={28}
        aria-valuemax={72}
        aria-valuenow={Math.round(editorRatio * 100)}
        tabIndex={0}
        onPointerDown={handleDividerPointerDown}
        onPointerMove={handleDividerPointerMove}
        onPointerUp={finishDividerResize}
        onPointerCancel={finishDividerResize}
        onLostPointerCapture={stopDividerResize}
        onKeyDown={handleDividerKeyDown}
        onDoubleClick={() => applyEditorRatio(DEFAULT_EDITOR_RATIO)}
      ><span aria-hidden="true">⠿</span></div>

      <section className="workspace-preview" aria-labelledby="workspace-preview-title">
        <div className="workspace-preview-heading">
          <strong id="workspace-preview-title">미리보기</strong>
          <DocumentActions result={isConverting ? null : result} title={title} onMessage={showToast} />
        </div>
        <iframe title={`${title} 미리보기`} srcDoc={result?.fullHtml ?? ""} />
        <footer className="workspace-statusbar is-preview"><span>{markdown.length.toLocaleString("ko-KR")}자</span><span>미리보기</span></footer>
      </section>
      {toast && <div className="toast">{toast}</div>}
    </main>
  );
}

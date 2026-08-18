import { type ChangeEvent, type DragEvent, useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../features/auth/AuthProvider";
import {
  createWorkspacePage,
  listWorkspacePages,
  updateWorkspacePage,
  type WorkspacePage,
} from "../../features/workspace/api";
import { copyMermaidPng } from "../../shared/export/clipboard";
import { convertMarkdown } from "../../shared/markdown/converter-core";
import type {
  ConversionMode,
  ConversionResult,
  ModeOption,
  UploadedMarkdownFile,
} from "../../shared/markdown/types";
import { DocumentActions } from "../../shared/ui/DocumentActions";
import { fileIcon } from "../../shared/ui/icons";
import { loadGuestDraft, saveGuestDraft, type GuestDraft } from "../workspace/guest-draft-store";
import { SAMPLE_MARKDOWN } from "./sample";
import { buildPreviewHtml } from "./preview";
import { loadQuickConversionDraft, saveQuickConversionDraft } from "./quick-conversion-draft-store";

const MODE_OPTIONS: ModeOption[] = [
  { id: "basic", title: "표준 변환", description: "일반적인 문서에 적합한 기본 스타일로 변환" },
  {
    id: "blank-lines",
    title: "빈 줄 추가",
    description: "문단, 제목, 코드블록 뒤에 에디터용 빈 줄 추가",
  },
  {
    id: "naver",
    title: "네이버 블로그",
    description: "네이버 에디터에 최적화된 코드블록 스타일 적용",
  },
];

const MAX_MARKDOWN_FILE_SIZE = 10 * 1024 * 1024;

function createSampleFile(): UploadedMarkdownFile {
  return {
    name: "sample-post.md",
    size: new Blob([SAMPLE_MARKDOWN]).size,
    text: SAMPLE_MARKDOWN,
    isSample: true,
  };
}

export function MarkdownPastePage() {
  const navigate = useNavigate();
  const { status: authStatus } = useAuth();
  const isAuthenticated = authStatus === "authenticated";
  const [initialDraft] = useState(loadQuickConversionDraft);
  const [markdownText, setMarkdownText] = useState(initialDraft?.markdownText ?? SAMPLE_MARKDOWN);
  const [currentFile, setCurrentFile] = useState<UploadedMarkdownFile>(initialDraft?.currentFile ?? createSampleFile);
  const [mode, setMode] = useState<ConversionMode>(initialDraft?.mode ?? "basic");
  const [excludeFirstH1, setExcludeFirstH1] = useState(initialDraft?.excludeFirstH1 ?? false);
  const [generateH2Toc, setGenerateH2Toc] = useState(initialDraft?.generateH2Toc ?? false);
  const [addH2Dividers, setAddH2Dividers] = useState(initialDraft?.addH2Dividers ?? false);
  const [result, setResult] = useState<ConversionResult | null>(null);
  const [previewRevision, setPreviewRevision] = useState(0);
  const [isConverting, setIsConverting] = useState(true);
  const [toast, setToast] = useState("");
  const [activeTab, setActiveTab] = useState<"preview" | "source">("preview");
  const [mobileSection, setMobileSection] = useState<"settings" | "result">("settings");
  const [isSaveDialogOpen, setIsSaveDialogOpen] = useState(false);
  const [saveMode, setSaveMode] = useState<"replace" | "append">("replace");
  const [existingGuestDraft, setExistingGuestDraft] = useState<GuestDraft | null>(null);
  const [workspacePages, setWorkspacePages] = useState<WorkspacePage[]>([]);
  const [workspaceSaveTarget, setWorkspaceSaveTarget] = useState("new");
  const [isSaving, setIsSaving] = useState(false);
  const previewFrameRef = useRef<HTMLIFrameElement>(null);
  const toastTimerRef = useRef<number | undefined>(undefined);

  const outputTitle = currentFile.name.replace(/\.(md|markdown)$/i, "") || "MD2Blog";

  const showToast = useCallback((message: string) => {
    window.clearTimeout(toastTimerRef.current);
    setToast(message);
    toastTimerRef.current = window.setTimeout(() => setToast(""), 2600);
  }, []);

  useEffect(() => {
    return () => window.clearTimeout(toastTimerRef.current);
  }, []);

  useEffect(() => {
    saveQuickConversionDraft({
      markdownText,
      currentFile,
      mode,
      excludeFirstH1,
      generateH2Toc,
      addH2Dividers,
    });
  }, [markdownText, currentFile, mode, excludeFirstH1, generateH2Toc, addH2Dividers]);

  useEffect(() => {
    let active = true;
    setIsConverting(true);

    void convertMarkdown(
      markdownText,
      mode,
      outputTitle,
      { excludeFirstH1, generateH2Toc, addH2Dividers },
      (partialResult) => {
        if (active) {
          setResult(partialResult);
          setPreviewRevision((revision) => revision + 1);
        }
      },
    )
      .then((nextResult) => {
        if (!active) return;
        setResult(nextResult);
        setPreviewRevision((revision) => revision + 1);
        setIsConverting(false);
      })
      .catch(() => {
        if (!active) return;
        setIsConverting(false);
        showToast("Markdown을 변환할 수 없습니다. 문서 내용을 확인해 주세요.");
      });

    return () => {
      active = false;
    };
  }, [markdownText, mode, outputTitle, excludeFirstH1, generateH2Toc, addH2Dividers, showToast]);

  useEffect(() => {
    const handlePreviewMessage = (event: MessageEvent) => {
      if (event.source !== previewFrameRef.current?.contentWindow) return;

      const data = event.data as { type?: unknown; svg?: unknown } | null;
      if (data?.type !== "copy-mermaid-png" || typeof data.svg !== "string") return;

      void copyMermaidPng(data.svg)
        .then(() => showToast("Mermaid 다이어그램을 PNG 이미지로 복사했습니다."))
        .catch(() => showToast("PNG 이미지를 복사할 수 없습니다. 브라우저 권한을 확인해 주세요."));
    };

    window.addEventListener("message", handlePreviewMessage);
    return () => window.removeEventListener("message", handlePreviewMessage);
  }, [showToast]);

  const loadMarkdownFile = async (file: File) => {
    if (!isMarkdownFile(file)) {
      showToast("Markdown 파일(.md, .markdown)만 업로드할 수 있습니다.");
      return;
    }

    if (file.size > MAX_MARKDOWN_FILE_SIZE) {
      showToast("10MB 이하의 Markdown 파일만 업로드할 수 있습니다.");
      return;
    }

    const text = await file.text();
    setCurrentFile({ name: file.name, size: file.size, text, isSample: false });
    setMarkdownText(text);
    setMobileSection("result");
    showToast(`${file.name} 파일을 불러왔습니다.`);
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.currentTarget.files?.[0];
    if (file) void loadMarkdownFile(file);
  };

  const handleDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    event.currentTarget.classList.remove("is-dragging");
    const file = event.dataTransfer.files[0];
    if (file) void loadMarkdownFile(file);
  };

  const resetSample = () => {
    const sampleFile = createSampleFile();
    setCurrentFile(sampleFile);
    setMarkdownText(sampleFile.text);
    showToast("샘플 Markdown 미리보기로 되돌렸습니다.");
  };

  const resetAll = () => {
    const sampleFile = createSampleFile();
    setCurrentFile(sampleFile);
    setMarkdownText(sampleFile.text);
    setMode("basic");
    setExcludeFirstH1(false);
    setGenerateH2Toc(false);
    setAddH2Dividers(false);
    setActiveTab("preview");
    showToast("빠른 변환 작업을 초기화했습니다.");
  };

  useEffect(() => {
    if (!isSaveDialogOpen) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !isSaving) setIsSaveDialogOpen(false);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isSaveDialogOpen, isSaving]);

  const openSaveDialog = async () => {
    if (authStatus === "loading") {
      showToast("로그인 상태를 확인하고 있습니다. 잠시 후 다시 시도해 주세요.");
      return;
    }
    try {
      setSaveMode("replace");
      if (isAuthenticated) {
        const pages = await listWorkspacePages();
        setWorkspacePages(pages);
        setWorkspaceSaveTarget("new");
      } else {
        setExistingGuestDraft(await loadGuestDraft());
      }
      setIsSaveDialogOpen(true);
    } catch {
      showToast("기록장 정보를 불러올 수 없습니다.");
    }
  };

  const confirmSaveToWorkspace = async () => {
    setIsSaving(true);
    try {
      if (isAuthenticated) {
        if (workspaceSaveTarget === "new") {
          await createWorkspacePage({
            title: outputTitle,
            content: markdownText,
            parent_id: null,
          });
        } else {
          const targetPage = workspacePages.find((page) => page.id === workspaceSaveTarget);
          if (!targetPage) throw new Error("저장 대상을 찾을 수 없습니다.");
          const existingMarkdown = targetPage.content.trimEnd();
          const nextMarkdown = saveMode === "append" && existingMarkdown
            ? `${existingMarkdown}\n\n${markdownText}`
            : markdownText;
          await updateWorkspacePage(targetPage.id, { content: nextMarkdown });
        }
        setIsSaveDialogOpen(false);
        navigate("/workspace");
        return;
      }

      const shouldAppend = saveMode === "append";
      const existingMarkdown = existingGuestDraft?.markdown.trimEnd() ?? "";
      const nextMarkdown = shouldAppend && existingMarkdown
        ? `${existingMarkdown}\n\n${markdownText}`
        : markdownText;
      await saveGuestDraft({
        title: "임시 페이지",
        markdown: nextMarkdown,
        updatedAt: Date.now(),
      });
      setIsSaveDialogOpen(false);
      navigate("/workspace");
    } catch {
      showToast("기록장에 저장할 수 없습니다.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <>
      <main className="converter-page">
        <div className="converter-mobile-tabs" role="tablist" aria-label="빠른 변환 화면">
          <button type="button" role="tab" aria-selected={mobileSection === "settings"} onClick={() => setMobileSection("settings")}>변환 설정</button>
          <button type="button" role="tab" aria-selected={mobileSection === "result"} onClick={() => setMobileSection("result")}>미리보기</button>
        </div>
        <div className={`layout mobile-section-${mobileSection}`}>
          <aside className="panel settings-panel" aria-label="변환 설정">
            <h2>
              <span>변환 설정</span>
              <button className="settings-reset-button" type="button" onClick={resetAll}>전체 초기화</button>
            </h2>
            <div className="settings-scroll">
              <section className="section">
                <h3 className="section-title">Markdown 파일 업로드</h3>
                <label
                  className="dropzone"
                  onDragOver={(event) => {
                    event.preventDefault();
                    event.currentTarget.classList.add("is-dragging");
                  }}
                  onDragLeave={(event) => event.currentTarget.classList.remove("is-dragging")}
                  onDrop={handleDrop}
                >
                  <input
                    className="file-input"
                    type="file"
                    aria-label="Markdown 파일 선택"
                    accept=".md,.markdown,text/markdown,text/plain"
                    onChange={handleFileChange}
                  />
                  <Icon html={fileIcon()} />
                  <p>파일을 드래그하거나 클릭하여 업로드</p>
                  <small>.md 파일만 지원 (최대 10MB)</small>
                </label>
                <div className="file-chip">
                  <span className="file-name">
                    <span className="success-dot" aria-hidden="true" />
                    <span>{currentFile.name}</span>
                  </span>
                  <span>{formatBytes(currentFile.size)}</span>
                  {!currentFile.isSample && (
                    <button
                      className="remove-file"
                      type="button"
                      title="샘플 미리보기로 되돌리기"
                      onClick={resetSample}
                    >
                      ×
                    </button>
                  )}
                </div>
              </section>

              <section className="section">
                <h3 className="section-title">변환 모드</h3>
                <div className="mode-list">
                  {MODE_OPTIONS.map((option) => (
                    <label className="mode-option" key={option.id}>
                      <input
                        type="radio"
                        name="conversion-mode"
                        value={option.id}
                        checked={mode === option.id}
                        onChange={() => setMode(option.id)}
                      />
                      <span>
                        <strong>{option.title}</strong>
                        <span>{option.description}</span>
                      </span>
                    </label>
                  ))}
                </div>
              </section>

              <section className="section conversion-options">
                <h3 className="section-title">추가 옵션</h3>
                <label>
                  <input type="checkbox" checked={excludeFirstH1} onChange={(event) => setExcludeFirstH1(event.target.checked)} />
                  <span><strong>첫 번째 제목(H1) 제외</strong></span>
                </label>
                <label>
                  <input type="checkbox" checked={generateH2Toc} onChange={(event) => setGenerateH2Toc(event.target.checked)} />
                  <span><strong>H2 목차 자동 생성</strong></span>
                </label>
                <label>
                  <input type="checkbox" checked={addH2Dividers} onChange={(event) => setAddH2Dividers(event.target.checked)} />
                  <span><strong>H2 구분선 추가</strong></span>
                </label>
              </section>

            </div>
          </aside>

          <div className="converter-main">
            <section className="panel preview-panel" aria-label="변환 결과">
              <div className="preview-header">
                <div className="preview-tabs" role="tablist" aria-label="변환 결과 보기">
                  <button type="button" role="tab" aria-selected={activeTab === "preview"} onClick={() => setActiveTab("preview")}>미리보기</button>
                  <button type="button" role="tab" aria-selected={activeTab === "source"} onClick={() => setActiveTab("source")}>원본 Markdown</button>
                </div>
                <DocumentActions result={isConverting ? null : result} title={outputTitle} onMessage={showToast} onSave={openSaveDialog} />
              </div>
              <div className="preview-wrap">
                {activeTab === "source" ? (
                  <pre className="markdown-source"><code>{markdownText}</code></pre>
                ) : result ? (
                  <iframe key={previewRevision} ref={previewFrameRef} className="preview-frame" title="변환 결과" sandbox="allow-scripts" srcDoc={buildPreviewHtml(result.fullHtml, "default")} />
                ) : null}
              </div>
            </section>
          </div>
        </div>
      </main>
      {isSaveDialogOpen && (
        <div
          className="save-dialog-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget && !isSaving) setIsSaveDialogOpen(false);
          }}
        >
          <section className="save-dialog" role="dialog" aria-modal="true" aria-labelledby="save-dialog-title">
            <h2 id="save-dialog-title">기록장에 저장</h2>
            {isAuthenticated ? (
              <>
                <p>새 페이지를 만들거나 기존 페이지에 저장할 수 있습니다.</p>
                <label className="save-dialog-select-label" htmlFor="workspace-save-target">저장 대상</label>
                <select
                  id="workspace-save-target"
                  className="save-dialog-select"
                  value={workspaceSaveTarget}
                  onChange={(event) => setWorkspaceSaveTarget(event.target.value)}
                >
                  <option value="new">새 페이지로 저장</option>
                  {workspacePages.map((page) => <option key={page.id} value={page.id}>{page.title}</option>)}
                </select>
              </>
            ) : <p>비회원은 임시 페이지 한 개만 사용할 수 있습니다.</p>}
            {(!isAuthenticated || workspaceSaveTarget !== "new") && <fieldset>
              <label>
                <input type="radio" name="save-mode" checked={saveMode === "replace"} onChange={() => setSaveMode("replace")} />
                <span>{isAuthenticated ? "선택한 페이지를 현재 내용으로 교체" : "임시 페이지를 현재 내용으로 교체"}</span>
              </label>
              {!isAuthenticated && saveMode === "replace" && existingGuestDraft?.markdown.trim() && (
                <small>기존 임시 페이지 내용이 현재 내용으로 교체됩니다.</small>
              )}
              <label>
                <input type="radio" name="save-mode" checked={saveMode === "append"} onChange={() => setSaveMode("append")} />
                <span>{isAuthenticated ? "선택한 페이지에 내용 추가" : "임시 페이지에 내용 추가"}</span>
              </label>
            </fieldset>}
            <div className="save-dialog-actions">
              <button type="button" onClick={() => setIsSaveDialogOpen(false)} disabled={isSaving}>취소</button>
              <button type="button" className="is-primary" onClick={() => void confirmSaveToWorkspace()} disabled={isSaving}>
                {isSaving ? "저장 중…" : (isAuthenticated ? "기록장에 저장" : "임시 페이지에 저장")}
              </button>
            </div>
          </section>
        </div>
      )}
      {toast && <div className="toast">{toast}</div>}
    </>
  );
}

function Icon({ html }: { html: string }) {
  return <span aria-hidden="true" dangerouslySetInnerHTML={{ __html: html }} />;
}

function isMarkdownFile(file: File): boolean {
  const lowerName = file.name.toLowerCase();
  return lowerName.endsWith(".md") || lowerName.endsWith(".markdown") || file.type === "text/markdown";
}

function formatBytes(bytes: number): string {
  return `${(bytes / 1024).toFixed(1)} KB`;
}

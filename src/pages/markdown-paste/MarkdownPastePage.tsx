import { type ChangeEvent, type DragEvent, useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
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
  const [markdownText, setMarkdownText] = useState(SAMPLE_MARKDOWN);
  const [currentFile, setCurrentFile] = useState<UploadedMarkdownFile>(createSampleFile);
  const [mode, setMode] = useState<ConversionMode>("basic");
  const [excludeFirstH1, setExcludeFirstH1] = useState(false);
  const [generateH2Toc, setGenerateH2Toc] = useState(false);
  const [addH2Dividers, setAddH2Dividers] = useState(false);
  const [result, setResult] = useState<ConversionResult | null>(null);
  const [toast, setToast] = useState("");
  const [activeTab, setActiveTab] = useState<"preview" | "source">("preview");
  const [isSaveDialogOpen, setIsSaveDialogOpen] = useState(false);
  const [saveMode, setSaveMode] = useState<"replace" | "append">("replace");
  const [existingGuestDraft, setExistingGuestDraft] = useState<GuestDraft | null>(null);
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
    let active = true;

    void convertMarkdown(markdownText, mode, outputTitle, { excludeFirstH1, generateH2Toc, addH2Dividers }).then((nextResult) => {
      if (active) setResult(nextResult);
    });

    return () => {
      active = false;
    };
  }, [markdownText, mode, outputTitle, excludeFirstH1, generateH2Toc, addH2Dividers]);

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

  useEffect(() => {
    if (!isSaveDialogOpen) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !isSaving) setIsSaveDialogOpen(false);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isSaveDialogOpen, isSaving]);

  const openSaveDialog = async () => {
    try {
      setExistingGuestDraft(await loadGuestDraft());
      setSaveMode("replace");
      setIsSaveDialogOpen(true);
    } catch {
      showToast("임시 페이지 정보를 불러올 수 없습니다.");
    }
  };

  const confirmSaveToWorkspace = async () => {
    setIsSaving(true);
    try {
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
      showToast("임시 페이지에 저장할 수 없습니다.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <>
      <main className="converter-page">
        <div className="layout">
          <aside className="panel settings-panel" aria-label="변환 설정">
            <h2>변환 설정</h2>
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
                <DocumentActions result={result} title={outputTitle} onMessage={showToast} onSave={openSaveDialog} />
              </div>
              <div className="preview-wrap">
                {activeTab === "source" ? (
                  <pre className="markdown-source"><code>{markdownText}</code></pre>
                ) : result ? (
                  <iframe ref={previewFrameRef} className="preview-frame" title="변환 결과" sandbox="allow-scripts" srcDoc={buildPreviewHtml(result.fullHtml, "default")} />
                ) : <div aria-live="polite">미리보기를 생성하고 있습니다.</div>}
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
            <p>비회원은 임시 페이지 한 개만 사용할 수 있습니다.</p>
            <fieldset>
              <label>
                <input type="radio" name="guest-save-mode" checked={saveMode === "replace"} onChange={() => setSaveMode("replace")} />
                <span>임시 페이지를 현재 내용으로 교체</span>
              </label>
              {saveMode === "replace" && existingGuestDraft?.markdown.trim() && (
                <small>기존 임시 페이지 내용이 현재 내용으로 교체됩니다.</small>
              )}
              <label>
                <input type="radio" name="guest-save-mode" checked={saveMode === "append"} onChange={() => setSaveMode("append")} />
                <span>임시 페이지에 내용 추가</span>
              </label>
            </fieldset>
            <div className="save-dialog-actions">
              <button type="button" onClick={() => setIsSaveDialogOpen(false)} disabled={isSaving}>취소</button>
              <button type="button" className="is-primary" onClick={() => void confirmSaveToWorkspace()} disabled={isSaving}>
                {isSaving ? "저장 중…" : "임시 페이지에 저장"}
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

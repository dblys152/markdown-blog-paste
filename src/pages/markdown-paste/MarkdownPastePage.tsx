import { type ChangeEvent, type DragEvent, useCallback, useEffect, useRef, useState } from "react";
import { copyMermaidPng, copyPreviewHtml } from "../../shared/export/clipboard";
import { downloadHtml } from "../../shared/export/html-export";
import { downloadPdf } from "../../shared/export/pdf-export";
import { convertMarkdown } from "../../shared/markdown/converter-core";
import type {
  ConversionMode,
  ConversionResult,
  ModeOption,
  PreviewStyle,
  UploadedMarkdownFile,
} from "../../shared/markdown/types";
import { APP_CSS } from "../../shared/styles/styles";
import { deviceIcon, fileIcon, githubIcon, lightbulbIcon, questionIcon } from "../../shared/ui/icons";
import { SAMPLE_MARKDOWN } from "./sample";
import { buildPreviewHtml } from "./preview";

const MODE_OPTIONS: ModeOption[] = [
  { id: "basic", title: "기본 변환", description: "Markdown을 기본 HTML로 변환합니다." },
  {
    id: "blank-lines",
    title: "빈 줄 추가",
    description: "문단, 제목, 코드블록 뒤에 에디터용 빈 줄을 추가합니다.",
  },
  {
    id: "naver",
    title: "네이버 블로그용",
    description: "네이버 에디터에 최적화된 코드블록 스타일과 빈 줄을 적용합니다.",
  },
];

const PREVIEW_STYLE_LABELS: Record<PreviewStyle, string> = {
  default: "기본",
  compact: "좁게",
  editor: "에디터",
};

function createSampleFile(): UploadedMarkdownFile {
  return {
    name: "sample-post.md",
    size: new Blob([SAMPLE_MARKDOWN]).size,
    text: SAMPLE_MARKDOWN,
    isSample: true,
  };
}

export function MarkdownPastePage() {
  const [markdownText, setMarkdownText] = useState(SAMPLE_MARKDOWN);
  const [currentFile, setCurrentFile] = useState<UploadedMarkdownFile>(createSampleFile);
  const [mode, setMode] = useState<ConversionMode>("basic");
  const [previewStyle, setPreviewStyle] = useState<PreviewStyle>("default");
  const [result, setResult] = useState<ConversionResult | null>(null);
  const [toast, setToast] = useState("");
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

    void convertMarkdown(markdownText, mode, outputTitle).then((nextResult) => {
      if (active) setResult(nextResult);
    });

    return () => {
      active = false;
    };
  }, [markdownText, mode, outputTitle]);

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

  const handlePreviewCopy = async () => {
    if (!result) return;
    const copiedType = await copyPreviewHtml(result.bodyHtml);
    showToast(
      copiedType === "html"
        ? "미리보기 HTML을 클립보드에 복사했습니다."
        : "미리보기 HTML을 텍스트로 복사했습니다.",
    );
  };

  const handlePdfDownload = async () => {
    if (!result) return;
    try {
      showToast("PDF 파일을 생성하고 있습니다.");
      await downloadPdf(result.bodyHtml, outputTitle);
      showToast("PDF 파일 다운로드를 시작했습니다.");
    } catch {
      showToast("PDF 파일을 만들 수 없습니다.");
    }
  };

  const resetSample = () => {
    const sampleFile = createSampleFile();
    setCurrentFile(sampleFile);
    setMarkdownText(sampleFile.text);
    showToast("샘플 Markdown 미리보기로 되돌렸습니다.");
  };

  return (
    <>
      <style>{APP_CSS}</style>
      <main className="app-shell">
        <header className="topbar">
          <div className="brand">
            <button
              className="brand-mark-button"
              type="button"
              title="새로고침"
              aria-label="새로고침"
              onClick={() => window.location.reload()}
            >
              <img className="brand-mark" src="/favicon.svg" alt="" aria-hidden="true" />
            </button>
            <div>
              <h1>
                <button
                  className="brand-title-button"
                  type="button"
                  title="새로고침"
                  onClick={() => window.location.reload()}
                >
                  MD2Blog
                </button>
              </h1>
              <p>Markdown 문서를 블로그 에디터에 붙여넣기 좋은 HTML로 변환합니다.</p>
            </div>
          </div>
          <div className="top-actions">
            <button
              className="secondary-button button-small"
              type="button"
              title="사용 가이드"
              onClick={() =>
                showToast("Markdown 파일을 올리고 변환 모드를 고른 뒤 복사하거나 HTML/PDF로 저장하세요.")
              }
            >
              <Icon html={questionIcon()} />
              <span>사용 가이드</span>
            </button>
            <a
              className="icon-button"
              href="https://github.com/dblys152/markdown-blog-paste"
              target="_blank"
              rel="noreferrer"
              title="GitHub"
            >
              <Icon html={githubIcon()} />
            </a>
          </div>
        </header>

        <div className="layout">
          <aside className="panel settings-panel" aria-label="변환 설정">
            <h2>변환 설정</h2>
            <div className="settings-scroll">
              <section className="section">
                <h3 className="section-title">1. Markdown 파일 업로드</h3>
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
                  <p>.md 파일을 선택하거나 드래그하세요</p>
                  <span className="primary-button button-small">파일 선택</span>
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
                <h3 className="section-title">2. 변환 모드 선택</h3>
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

              <section className="section">
                <h3 className="section-title">3. 작업</h3>
                <div className="action-stack">
                  <button className="secondary-button" type="button" disabled={!result} onClick={handlePreviewCopy}>
                    <span aria-hidden="true">⧉</span>
                    <span>미리보기 내용 복사</span>
                  </button>
                  <button
                    className="secondary-button"
                    type="button"
                    disabled={!result}
                    onClick={() => {
                      if (!result) return;
                      downloadHtml(result.fullHtml, outputTitle);
                      showToast("HTML 파일 다운로드를 시작했습니다.");
                    }}
                  >
                    <span aria-hidden="true">⇩</span>
                    <span>HTML 파일 다운로드</span>
                  </button>
                  <button
                    className="secondary-button"
                    type="button"
                    disabled={!result}
                    onClick={() => void handlePdfDownload()}
                  >
                    <span aria-hidden="true">⇩</span>
                    <span>PDF 다운로드</span>
                  </button>
                </div>
              </section>

              <div className="tip">
                <div className="tip-title">
                  <Icon html={lightbulbIcon()} />
                  <strong>Tip</strong>
                </div>
                <p>미리보기 내용을 복사해서 티스토리, 네이버 블로그 에디터에 붙여넣기(Ctrl+V) 하세요.</p>
              </div>
            </div>
          </aside>

          <section className="panel preview-panel" aria-label="변환 결과 미리보기">
            <div className="preview-header">
              <h2 className="preview-title">변환 결과 미리보기</h2>
              <div className="preview-controls">
                <label>
                  <Icon html={deviceIcon()} />
                  <span>미리보기 스타일</span>
                  <select
                    aria-label="미리보기 스타일"
                    value={previewStyle}
                    onChange={(event) => setPreviewStyle(event.target.value as PreviewStyle)}
                  >
                    {Object.entries(PREVIEW_STYLE_LABELS).map(([value, label]) => (
                      <option value={value} key={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </div>
            <div className="preview-wrap">
              {result ? (
                <iframe
                  ref={previewFrameRef}
                  className="preview-frame"
                  title="변환 결과"
                  sandbox="allow-scripts"
                  srcDoc={buildPreviewHtml(result.fullHtml, previewStyle)}
                />
              ) : (
                <div aria-live="polite">미리보기를 생성하고 있습니다.</div>
              )}
            </div>
          </section>
        </div>
      </main>
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

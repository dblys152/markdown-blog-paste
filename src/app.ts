import { convertMarkdown } from "./converter-core";
import { APP_CSS } from "./styles";
import type { ConversionMode, ModeOption, PreviewStyle, UploadedMarkdownFile } from "./types";

const SAMPLE_MARKDOWN = `# Markdown Blog Post 예시

이 문서는 마크다운 문서가 블로그에 어떻게 표시되는지 보여주는 예시입니다.

---

## 1. 제목 스타일

H1, H2, H3 제목이 어떻게 변환되는지 확인할 수 있습니다.

### H3 제목입니다

## 2. 목록

- 순서 없는 목록 아이템 1
- 순서 없는 목록 아이템 2
  - 중첩 아이템 2-1
  - 중첩 아이템 2-2

1. 순서 있는 목록 아이템 1
2. 순서 있는 목록 아이템 2

## 3. 코드 블록

일반 코드 블록입니다.

\`\`\`ts
function hello(name: string) {
  console.log(\`Hello, \${name}!\`);
}
\`\`\`

## 4. 인용문

> 인용문은 이렇게 표시됩니다.

## 5. 표

| 이름 | 나이 | 직업 |
|---|---:|---|
| 홍길동 | 30 | 개발자 |
| 김영희 | 28 | 디자이너 |
`;

const MODE_OPTIONS: ModeOption[] = [
  {
    id: "basic",
    title: "기본 변환",
    description: "Markdown을 기본 HTML로 변환합니다.",
  },
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

let markdownText = SAMPLE_MARKDOWN;
let currentFile: UploadedMarkdownFile = {
  name: "sample-post.md",
  size: new Blob([SAMPLE_MARKDOWN]).size,
  text: SAMPLE_MARKDOWN,
  isSample: true,
};
let mode: ConversionMode = "basic";
let previewStyle: PreviewStyle = "default";
let toastTimer: number | undefined;

const appRoot = document.querySelector<HTMLDivElement>("#app");

if (!appRoot) {
  throw new Error("App root not found.");
}

const app = appRoot;

injectStyles();
render();

function render(): void {
  const result = convertMarkdown(markdownText, mode, getOutputTitle());

  app.innerHTML = `
    <main class="app-shell">
      <header class="topbar">
        <div class="brand">
          <img class="brand-mark" src="/favicon.svg" alt="" aria-hidden="true" />
          <div>
            <h1>markdown-blog-paste</h1>
            <p>Markdown 문서를 블로그 에디터에 붙여넣기 좋은 HTML로 변환합니다.</p>
          </div>
        </div>
        <div class="top-actions">
          <button class="secondary-button button-small" type="button" data-action="guide" title="사용 가이드">
            ${questionIcon()}
            <span>사용 가이드</span>
          </button>
          <a class="icon-button" href="https://github.com/dblys152/markdown-blog-paste" target="_blank" rel="noreferrer" title="GitHub">
            ${githubIcon()}
          </a>
        </div>
      </header>

      <div class="layout">
        <aside class="panel settings-panel" aria-label="변환 설정">
          <h2>변환 설정</h2>

          <section class="section">
            <h3 class="section-title">1. Markdown 파일 업로드</h3>
            <label class="dropzone" data-dropzone>
              <input class="file-input" data-file-input type="file" accept=".md,.markdown,text/markdown,text/plain" />
              <div aria-hidden="true">${fileIcon()}</div>
              <p>.md 파일을 선택하거나 드래그하세요</p>
              <span class="primary-button button-small">파일 선택</span>
            </label>
            ${renderFileChip()}
          </section>

          <section class="section">
            <h3 class="section-title">2. 변환 모드 선택</h3>
            <div class="mode-list">
              ${MODE_OPTIONS.map(renderModeOption).join("")}
            </div>
          </section>

          <section class="section">
            <h3 class="section-title">3. 작업</h3>
            <div class="action-stack">
              <button class="secondary-button" type="button" data-action="copy">
                <span aria-hidden="true">⧉</span>
                <span>미리보기 내용 복사</span>
              </button>
              <button class="secondary-button" type="button" data-action="download">
                <span aria-hidden="true">⇩</span>
                <span>HTML 파일 다운로드</span>
              </button>
            </div>
          </section>

          <div class="tip">
            <div class="tip-title">
              ${lightbulbIcon()}
              <strong>Tip</strong>
            </div>
            <p>미리보기 내용을 복사해서 티스토리, 네이버 블로그 에디터에 붙여넣기(Ctrl+V) 하세요.</p>
          </div>
        </aside>

        <section class="panel preview-panel" aria-label="변환 결과 미리보기">
          <div class="preview-header">
            <h2 class="preview-title">변환 결과 미리보기</h2>
            <div class="preview-controls">
              <label>
                ${deviceIcon()}
                <span>미리보기 스타일</span>
                <select data-preview-style>
                  ${Object.entries(PREVIEW_STYLE_LABELS)
                    .map(
                      ([value, label]) =>
                        `<option value="${value}" ${previewStyle === value ? "selected" : ""}>${label}</option>`,
                    )
                    .join("")}
                </select>
              </label>
            </div>
          </div>
          <div class="preview-wrap">
            <iframe class="preview-frame" title="변환 결과" sandbox srcdoc="${escapeSrcdoc(
              applyPreviewStyle(result.fullHtml),
            )}"></iframe>
          </div>
        </section>
      </div>
    </main>
  `;

  bindEvents(result.bodyHtml, result.fullHtml);
}

function bindEvents(bodyHtml: string, fullHtml: string): void {
  app.querySelector<HTMLInputElement>("[data-file-input]")?.addEventListener("change", (event) => {
    const input = event.currentTarget as HTMLInputElement;
    const file = input.files?.[0];

    if (file) {
      void loadMarkdownFile(file);
    }
  });

  const dropzone = app.querySelector<HTMLElement>("[data-dropzone]");
  dropzone?.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropzone.classList.add("is-dragging");
  });
  dropzone?.addEventListener("dragleave", () => {
    dropzone.classList.remove("is-dragging");
  });
  dropzone?.addEventListener("drop", (event) => {
    event.preventDefault();
    dropzone.classList.remove("is-dragging");
    const file = event.dataTransfer?.files[0];

    if (file) {
      void loadMarkdownFile(file);
    }
  });

  app.querySelectorAll<HTMLInputElement>("[name='conversion-mode']").forEach((input) => {
    input.addEventListener("change", () => {
      mode = input.value as ConversionMode;
      render();
    });
  });

  app.querySelector<HTMLButtonElement>("[data-action='reset-sample']")?.addEventListener("click", () => {
    currentFile = {
      name: "sample-post.md",
      size: new Blob([SAMPLE_MARKDOWN]).size,
      text: SAMPLE_MARKDOWN,
      isSample: true,
    };
    markdownText = SAMPLE_MARKDOWN;
    render();
    showToast("샘플 Markdown 미리보기로 되돌렸습니다.");
  });

  app.querySelector<HTMLSelectElement>("[data-preview-style]")?.addEventListener("change", (event) => {
    const select = event.currentTarget as HTMLSelectElement;
    previewStyle = select.value as PreviewStyle;
    render();
  });

  app.querySelector<HTMLButtonElement>("[data-action='copy']")?.addEventListener("click", () => {
    void copyPreviewHtml(bodyHtml);
  });

  app.querySelector<HTMLButtonElement>("[data-action='download']")?.addEventListener("click", () => {
    downloadHtml(fullHtml);
  });

  app.querySelector<HTMLButtonElement>("[data-action='guide']")?.addEventListener("click", () => {
    showToast("Markdown 파일을 올리고 변환 모드를 고른 뒤 복사하거나 HTML로 저장하세요.");
  });
}

async function loadMarkdownFile(file: File): Promise<void> {
  if (!isMarkdownFile(file)) {
    showToast("Markdown 파일(.md, .markdown)만 업로드할 수 있습니다.");
    return;
  }

  const text = await file.text();
  currentFile = {
    name: file.name,
    size: file.size,
    text,
    isSample: false,
  };
  markdownText = text;
  render();
  showToast(`${file.name} 파일을 불러왔습니다.`);
}

async function copyPreviewHtml(bodyHtml: string): Promise<void> {
  try {
    if ("ClipboardItem" in window && navigator.clipboard?.write) {
      const htmlBlob = new Blob([bodyHtml], { type: "text/html" });
      const textBlob = new Blob([stripHtml(bodyHtml)], { type: "text/plain" });
      await navigator.clipboard.write([
        new ClipboardItem({
          "text/html": htmlBlob,
          "text/plain": textBlob,
        }),
      ]);
    } else {
      await navigator.clipboard.writeText(bodyHtml);
    }

    showToast("미리보기 HTML을 클립보드에 복사했습니다.");
  } catch {
    fallbackCopy(bodyHtml);
    showToast("미리보기 HTML을 텍스트로 복사했습니다.");
  }
}

function fallbackCopy(value: string): void {
  const textarea = document.createElement("textarea");
  textarea.value = value;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  document.body.append(textarea);
  textarea.select();
  document.execCommand("copy");
  textarea.remove();
}

function downloadHtml(fullHtml: string): void {
  const blob = new Blob([fullHtml], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${getOutputTitle()}.html`;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  showToast("HTML 파일 다운로드를 시작했습니다.");
}

function renderModeOption(option: ModeOption): string {
  return `
    <label class="mode-option">
      <input type="radio" name="conversion-mode" value="${option.id}" ${mode === option.id ? "checked" : ""} />
      <span>
        <strong>${option.title}</strong>
        <span>${option.description}</span>
      </span>
    </label>
  `;
}

function renderFileChip(): string {
  return `
    <div class="file-chip">
      <span class="file-name">
        <span class="success-dot" aria-hidden="true"></span>
        <span>${escapeHtml(currentFile.name)}</span>
      </span>
      <span>${formatBytes(currentFile.size)}</span>
      ${
        currentFile.isSample
          ? ""
          : '<button class="remove-file" type="button" data-action="reset-sample" title="샘플 미리보기로 되돌리기">×</button>'
      }
    </div>
  `;
}

function applyPreviewStyle(fullHtml: string): string {
  if (previewStyle === "compact") {
    return fullHtml.replace("max-width: 760px;", "max-width: 620px;");
  }

  if (previewStyle === "editor") {
    return fullHtml.replace(
      "</style>",
      `
body {
  margin-top: 20px;
  margin-bottom: 20px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
}
</style>`,
    );
  }

  return fullHtml;
}

function isMarkdownFile(file: File): boolean {
  const lowerName = file.name.toLowerCase();
  return lowerName.endsWith(".md") || lowerName.endsWith(".markdown") || file.type === "text/markdown";
}

function getOutputTitle(): string {
  return currentFile.name.replace(/\.(md|markdown)$/i, "") || "markdown-blog-paste";
}

function stripHtml(value: string): string {
  const template = document.createElement("template");
  template.innerHTML = value;
  return template.content.textContent?.trim() ?? "";
}

function showToast(message: string): void {
  window.clearTimeout(toastTimer);
  app.querySelector(".toast")?.remove();
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  app.append(toast);
  toastTimer = window.setTimeout(() => toast.remove(), 2600);
}

function formatBytes(bytes: number): string {
  return `${(bytes / 1024).toFixed(1)} KB`;
}

function escapeSrcdoc(value: string): string {
  return value.replaceAll("&", "&amp;").replaceAll('"', "&quot;");
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function injectStyles(): void {
  const style = document.createElement("style");
  style.textContent = APP_CSS;
  document.head.append(style);
}

function fileIcon(): string {
  return `
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z" stroke="#374151" stroke-width="1.8" stroke-linejoin="round"/>
      <path d="M14 2v6h6" stroke="#374151" stroke-width="1.8" stroke-linejoin="round"/>
    </svg>
  `;
}

function questionIcon(): string {
  return `
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2"/>
      <path d="M9.8 9.3a2.3 2.3 0 1 1 3.7 1.8c-.9.6-1.5 1.1-1.5 2.4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      <path d="M12 17h.01" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>
    </svg>
  `;
}

function githubIcon(): string {
  return `
    <svg width="25" height="25" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 .5C5.7.5.6 5.6.6 11.9c0 5 3.3 9.3 7.9 10.8.6.1.8-.3.8-.6v-2c-3.2.7-3.9-1.4-3.9-1.4-.5-1.3-1.3-1.7-1.3-1.7-1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 .1.8 2.4 3.1 1.7.1-.8.4-1.3.7-1.6-2.6-.3-5.3-1.3-5.3-5.7 0-1.3.5-2.3 1.2-3.1-.1-.3-.5-1.5.1-3.1 0 0 1-.3 3.2 1.2.9-.3 1.9-.4 2.9-.4s2 .1 2.9.4c2.2-1.5 3.2-1.2 3.2-1.2.6 1.6.2 2.8.1 3.1.8.8 1.2 1.9 1.2 3.1 0 4.4-2.7 5.4-5.3 5.7.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6 4.6-1.5 7.9-5.8 7.9-10.8C23.4 5.6 18.3.5 12 .5Z"/>
    </svg>
  `;
}

function lightbulbIcon(): string {
  return `
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M9 18h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      <path d="M10 22h4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      <path d="M8.6 14.7A6 6 0 1 1 15.4 14c-.9.7-1.4 1.6-1.4 2.7h-4c0-.9-.5-1.6-1.4-2Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
    </svg>
  `;
}

function deviceIcon(): string {
  return `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="7" y="2.5" width="10" height="19" rx="2" stroke="currentColor" stroke-width="2"/>
      <path d="M10.5 5.5h3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      <path d="M11.5 18.5h1" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/>
    </svg>
  `;
}

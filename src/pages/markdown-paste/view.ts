import type {
  ConversionResult,
  ConversionMode,
  ModeOption,
  PreviewStyle,
  UploadedMarkdownFile,
} from "../../shared/markdown/types";
import { deviceIcon, fileIcon, githubIcon, lightbulbIcon, questionIcon } from "../../shared/ui/icons";

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

interface MarkdownPasteViewProps {
  currentFile: UploadedMarkdownFile;
  mode: ConversionMode;
  previewStyle: PreviewStyle;
  result: ConversionResult;
}

export function renderMarkdownPasteView({
  currentFile,
  mode,
  previewStyle,
  result,
}: MarkdownPasteViewProps): string {
  return `
    <main class="app-shell">
      <header class="topbar">
        <div class="brand">
          <img class="brand-mark" src="/favicon.svg" alt="" aria-hidden="true" />
          <div>
            <h1>MD2Blog</h1>
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
            ${renderFileChip(currentFile)}
          </section>

          <section class="section">
            <h3 class="section-title">2. 변환 모드 선택</h3>
            <div class="mode-list">
              ${MODE_OPTIONS.map((option) => renderModeOption(option, mode)).join("")}
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
              <button class="secondary-button" type="button" data-action="download-pdf">
                <span aria-hidden="true">⇩</span>
                <span>PDF 다운로드</span>
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
            <iframe class="preview-frame" title="변환 결과" sandbox="allow-scripts" srcdoc="${escapeSrcdoc(
              applyPreviewStyle(result.fullHtml, previewStyle),
            )}"></iframe>
          </div>
        </section>
      </div>
    </main>
  `;
}

function renderModeOption(option: ModeOption, mode: ConversionMode): string {
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

function renderFileChip(currentFile: UploadedMarkdownFile): string {
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

function applyPreviewStyle(fullHtml: string, previewStyle: PreviewStyle): string {
  if (previewStyle === "compact") {
    return fullHtml.replaceAll("max-width: 800px;", "max-width: 660px;");
  }

  if (previewStyle === "editor") {
    return fullHtml.replace(
      "</style>",
      `
.document-layout {
  margin-top: 20px;
  margin-bottom: 20px;
}

.document-content {
  padding: 20px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
}
</style>`,
    );
  }

  return fullHtml;
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

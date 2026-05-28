import { copyPreviewHtml } from "../../shared/export/clipboard";
import { downloadHtml } from "../../shared/export/html-export";
import { downloadPdf } from "../../shared/export/pdf-export";
import { convertMarkdown } from "../../shared/markdown/converter-core";
import type { ConversionMode, PreviewStyle, UploadedMarkdownFile } from "../../shared/markdown/types";
import { APP_CSS } from "../../shared/styles/styles";
import { createToast } from "../../shared/ui/toast";
import { SAMPLE_MARKDOWN } from "./sample";
import { renderMarkdownPasteView } from "./view";

let markdownText = SAMPLE_MARKDOWN;
let currentFile: UploadedMarkdownFile = {
  name: "sample-post.md",
  size: new Blob([SAMPLE_MARKDOWN]).size,
  text: SAMPLE_MARKDOWN,
  isSample: true,
};
let mode: ConversionMode = "basic";
let previewStyle: PreviewStyle = "default";
let showToast: (message: string) => void;

export function mountMarkdownPastePage(selector: string): void {
  const appRoot = document.querySelector<HTMLDivElement>(selector);

  if (!appRoot) {
    throw new Error("App root not found.");
  }

  app = appRoot;
  showToast = createToast(app);

  injectStyles();
  render();
}

let app: HTMLDivElement;

function render(): void {
  const result = convertMarkdown(markdownText, mode, getOutputTitle());

  app.innerHTML = renderMarkdownPasteView({
    currentFile,
    mode,
    previewStyle,
    result,
  });

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
    void handlePreviewCopy(bodyHtml);
  });

  app.querySelector<HTMLButtonElement>("[data-action='download']")?.addEventListener("click", () => {
    handleHtmlDownload(fullHtml);
  });

  app.querySelector<HTMLButtonElement>("[data-action='download-pdf']")?.addEventListener("click", () => {
    void handlePdfDownload(bodyHtml);
  });

  app.querySelector<HTMLButtonElement>("[data-action='guide']")?.addEventListener("click", () => {
    showToast("Markdown 파일을 올리고 변환 모드를 고른 뒤 복사하거나 HTML/PDF로 저장하세요.");
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

async function handlePreviewCopy(bodyHtml: string): Promise<void> {
  const copiedType = await copyPreviewHtml(bodyHtml);

  if (copiedType === "html") {
    showToast("미리보기 HTML을 클립보드에 복사했습니다.");
    return;
  }

  showToast("미리보기 HTML을 텍스트로 복사했습니다.");
}

function handleHtmlDownload(fullHtml: string): void {
  downloadHtml(fullHtml, getOutputTitle());
  showToast("HTML 파일 다운로드를 시작했습니다.");
}

async function handlePdfDownload(bodyHtml: string): Promise<void> {
  try {
    showToast("PDF 파일을 생성하고 있습니다.");
    await downloadPdf(bodyHtml, getOutputTitle());
    showToast("PDF 파일 다운로드를 시작했습니다.");
  } catch {
    showToast("PDF 파일을 만들 수 없습니다.");
  }
}

function isMarkdownFile(file: File): boolean {
  const lowerName = file.name.toLowerCase();
  return lowerName.endsWith(".md") || lowerName.endsWith(".markdown") || file.type === "text/markdown";
}

function getOutputTitle(): string {
  return currentFile.name.replace(/\.(md|markdown)$/i, "") || "markdown-blog-paste";
}

function injectStyles(): void {
  const style = document.createElement("style");
  style.textContent = APP_CSS;
  document.head.append(style);
}

import { marked } from "marked";
import type { ConversionMode, ConversionOptions, ConversionResult, TocEntry } from "./types";
import {
  addEditorBlankLines,
  applyBlogInlineStyles,
  convertCodeBlocksForNaver,
  type PostProcessor,
} from "./processors";
import { addHeadingAnchors } from "./toc";
import { renderFloatingSectionNav } from "./floating-section-nav";
import { BASE_CSS } from "../styles/styles";
import { renderMermaidDiagrams } from "./mermaid-renderer";

const HTML_LANG = "ko";
const HTML_CHARSET = "UTF-8";

marked.use({
  gfm: true,
  breaks: true,
});

export function renderBaseMarkdown(markdownText: string): string {
  return marked.parse(markdownText, { async: false }) as string;
}

export async function renderMarkdown(
  markdownText: string,
  postProcessors: PostProcessor[] = [],
  onProgress?: (bodyHtml: string) => void,
): Promise<string> {
  const processHtml = (html: string) => {
    let bodyHtml = applyBlogInlineStyles(html);

    for (const processor of postProcessors) {
      bodyHtml = processor(bodyHtml);
    }

    return bodyHtml;
  };

  const bodyHtml = await renderMermaidDiagrams(
    renderBaseMarkdown(markdownText),
    (partialHtml) => onProgress?.(processHtml(partialHtml)),
  );

  return processHtml(bodyHtml);
}

export async function convertMarkdown(
  markdownText: string,
  mode: ConversionMode,
  title = "MD2Blog",
  options: ConversionOptions = { excludeFirstH1: false, generateH2Toc: false, addH2Dividers: false },
  onProgress?: (result: ConversionResult) => void,
): Promise<ConversionResult> {
  const processors = getPostProcessors(mode);
  const createResult = (renderedHtml: string): ConversionResult => {
    let bodyHtml = applyConversionOptions(renderedHtml, options);

    for (const processor of processors) {
      bodyHtml = processor(bodyHtml);
    }

    return {
      bodyHtml,
      fullHtml: wrapHtml(bodyHtml, title),
    };
  };

  const renderedHtml = await renderMarkdown(
    markdownText,
    [],
    (partialHtml) => onProgress?.(createResult(partialHtml)),
  );

  return createResult(renderedHtml);
}

function applyConversionOptions(bodyHtml: string, options: ConversionOptions): string {
  if (!options.excludeFirstH1 && !options.generateH2Toc && !options.addH2Dividers) return bodyHtml;

  const anchoredContent = addHeadingAnchors(bodyHtml);
  const template = document.createElement("template");
  template.innerHTML = anchoredContent.bodyHtml;

  if (options.excludeFirstH1) {
    template.content.querySelector("h1")?.remove();
  }

  const headings = Array.from(template.content.querySelectorAll("h2"));

  if (options.addH2Dividers) {
    headings.slice(1).forEach((heading) => {
      const divider = document.createElement("hr");
      divider.className = "h2-section-divider";
      divider.setAttribute("style", "border:0;border-top:1px solid #e5e7eb;margin:36px 0;");
      heading.before(divider);
    });
  }

  if (options.generateH2Toc && headings.length > 0) {
    const h2Entries = anchoredContent.entries.filter((entry): entry is TocEntry => entry.level === 2);
    const tocTitle = document.createElement("h2");
    tocTitle.className = "h2-toc-title";
    tocTitle.textContent = "목차";
    tocTitle.setAttribute("style", "margin:44px 0 20px;font-size:24px;line-height:1.4;font-weight:800;color:#222;");
    const list = document.createElement("ol");
    list.className = "h2-toc-list";
    list.setAttribute("style", "margin:0 0 36px;padding-left:28px;");

    h2Entries.forEach((entry) => {
      const item = document.createElement("li");
      item.className = "h2-toc-item";
      item.textContent = entry.text.replace(/^\d+[.)]\s*/, "");
      item.setAttribute("style", "margin:0 0 10px;padding-left:4px;color:#2d2f33;font-size:18px;line-height:1.65;");
      list.append(item);
    });

    headings[0]?.before(tocTitle, list);

    if (options.addH2Dividers) {
      const tocDivider = document.createElement("hr");
      tocDivider.className = "h2-toc-divider";
      tocDivider.setAttribute("style", "border:0;border-top:1px solid #e5e7eb;margin:36px 0;");
      list.after(tocDivider);
    }
  }

  return template.innerHTML;
}

export function wrapHtml(bodyHtml: string, title: string): string {
  const safeTitle = escapeAttribute(title);
  const anchoredContent = addHeadingAnchors(bodyHtml);

  return `<!DOCTYPE html>
<html lang="${HTML_LANG}">
<head>
  <meta charset="${HTML_CHARSET}" />
  <title>${safeTitle}</title>
  <style>
${BASE_CSS}
  </style>
</head>
<body>
  <div class="document-layout">
    <main class="document-content">
${anchoredContent.bodyHtml}
    </main>
  </div>
  ${renderFloatingSectionNav(anchoredContent.entries)}
</body>
</html>
`;
}

function getPostProcessors(mode: ConversionMode): PostProcessor[] {
  if (mode === "blank-lines") {
    return [addEditorBlankLines];
  }

  if (mode === "naver") {
    return [convertCodeBlocksForNaver, addEditorBlankLines];
  }

  return [];
}

function escapeAttribute(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

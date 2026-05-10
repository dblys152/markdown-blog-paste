import { marked } from "marked";
import type { ConversionMode, ConversionResult } from "./types";
import {
  addEditorBlankLines,
  applyBlogInlineStyles,
  convertCodeBlocksForNaver,
  type PostProcessor,
} from "./processors";
import { BASE_CSS } from "./styles";

const HTML_LANG = "ko";
const HTML_CHARSET = "UTF-8";

marked.use({
  gfm: true,
  breaks: true,
});

export function renderBaseMarkdown(markdownText: string): string {
  return marked.parse(markdownText, { async: false }) as string;
}

export function renderMarkdown(
  markdownText: string,
  postProcessors: PostProcessor[] = [],
): string {
  let bodyHtml = applyBlogInlineStyles(renderBaseMarkdown(markdownText));

  for (const processor of postProcessors) {
    bodyHtml = processor(bodyHtml);
  }

  return bodyHtml;
}

export function convertMarkdown(
  markdownText: string,
  mode: ConversionMode,
  title = "markdown-blog-paste",
): ConversionResult {
  const processors = getPostProcessors(mode);
  const bodyHtml = renderMarkdown(markdownText, processors);

  return {
    bodyHtml,
    fullHtml: wrapHtml(bodyHtml, title),
  };
}

export function wrapHtml(bodyHtml: string, title: string): string {
  const safeTitle = escapeAttribute(title);

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
${bodyHtml}
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

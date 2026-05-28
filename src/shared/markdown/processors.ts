export const EDITOR_SPACER = '<p class="editor-spacer">&nbsp;</p>';
export const CODE_BLOCK_SPACER_MARKER = "<!--EDITOR_SPACER_AFTER_CODE_BLOCK-->";

const BLOCK_END_TAGS = ["</p>", "</blockquote>", "</pre>", "</table>", "</ul>", "</ol>"];
const HEADING_END_TAGS = ["</h2>", "</h3>"];

const NAVER_CODE_BLOCK_STYLE = [
  "font-family: Consolas, Monaco, 'Courier New', monospace;",
  "font-size: 15px;",
  "line-height: 1.75;",
  "color: #111827;",
  "background-color: #f8f9fa;",
  "border: 1px solid #d1d5db;",
  "border-radius: 8px;",
  "padding: 18px;",
  "margin: 24px 0;",
  "white-space: normal;",
  "overflow-x: auto;",
].join("");

export type PostProcessor = (htmlText: string) => string;

export function applyBlogInlineStyles(htmlText: string): string {
  const template = document.createElement("template");
  template.innerHTML = htmlText;

  template.content.querySelectorAll("h1").forEach((heading) => {
    mergeInlineStyle(
      heading as HTMLElement,
      "font-size: 28px; margin-top: 44px; margin-bottom: 24px; line-height: 1.4;",
    );
  });

  template.content.querySelectorAll("h2").forEach((heading) => {
    mergeInlineStyle(
      heading as HTMLElement,
      "font-size: 24px; margin-top: 44px; margin-bottom: 20px; line-height: 1.4;",
    );
  });

  template.content.querySelectorAll("h3").forEach((heading) => {
    mergeInlineStyle(
      heading as HTMLElement,
      "font-size: 19px; margin-top: 36px; margin-bottom: 16px; line-height: 1.5;",
    );
  });

  template.content.querySelectorAll("table").forEach((table) => {
    mergeInlineStyle(
      table as HTMLElement,
      "border-collapse: collapse; width: 100%; margin: 24px 0; font-size: 15px;",
    );
  });

  template.content.querySelectorAll("th, td").forEach((cell) => {
    mergeInlineStyle(
      cell as HTMLElement,
      "border: 1px solid #ddd; padding: 10px 12px; line-height: 1.7;",
    );
  });

  template.content.querySelectorAll("th").forEach((headerCell) => {
    mergeInlineStyle(headerCell as HTMLElement, "background: #f5f5f5; font-weight: 700;");
  });

  return template.innerHTML;
}

export function addEditorBlankLines(htmlText: string): string {
  let converted = htmlText;

  for (const tag of BLOCK_END_TAGS) {
    converted = converted.replaceAll(tag, `${tag}\n${EDITOR_SPACER}`);
  }

  for (const tag of HEADING_END_TAGS) {
    converted = converted.replaceAll(tag, `${tag}\n${EDITOR_SPACER}`);
  }

  return converted.replaceAll(CODE_BLOCK_SPACER_MARKER, EDITOR_SPACER);
}

export function convertCodeBlocksForNaver(htmlText: string): string {
  const codeBlockPattern = /<pre><code(?: class="language-([^"]+)")?>([\s\S]*?)<\/code><\/pre>/g;

  return htmlText.replace(codeBlockPattern, (_match, _language, codeText: string) => {
    const preservedCode = preserveCodeSpacing(codeText);

    return `<div style="${NAVER_CODE_BLOCK_STYLE}">${preservedCode}</div>\n${CODE_BLOCK_SPACER_MARKER}`;
  });
}

function preserveCodeSpacing(codeText: string): string {
  const unescaped = decodeHtmlEntities(codeText).replace(/\n$/, "");
  const escaped = escapeHtml(unescaped);

  return escaped
    .replaceAll("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
    .replaceAll(" ", "&nbsp;")
    .replaceAll("\n", "<br>");
}

function decodeHtmlEntities(value: string): string {
  const textarea = document.createElement("textarea");
  textarea.innerHTML = value;
  return textarea.value;
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function mergeInlineStyle(element: HTMLElement, styleText: string): void {
  const currentStyle = element.getAttribute("style");
  element.setAttribute("style", currentStyle ? `${currentStyle}; ${styleText}` : styleText);
}

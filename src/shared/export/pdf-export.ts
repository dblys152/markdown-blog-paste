import { createScopedContentCss } from "../styles/styles";

const PRINT_FRAME_CLEANUP_DELAY_MS = 60_000;

const PDF_PRINT_CSS = `
${createScopedContentCss(".pdf-document", "print")}

@page {
  size: A4 portrait;
  margin: 14mm;
}

html,
body {
  margin: 0;
  padding: 0;
  background: #fff;
}

`.trim();

export function createPrintableHtml(bodyHtml: string, title: string): string {
  const printBodyHtml = normalizePrintBodyHtml(bodyHtml);

  return `<!doctype html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(title)}</title>
  <style>${PDF_PRINT_CSS}</style>
</head>
<body>
  <article class="pdf-document">${printBodyHtml}</article>
</body>
</html>`;
}

export async function openPdfPrintDialog(bodyHtml: string, title: string): Promise<void> {
  const frame = document.createElement("iframe");
  frame.setAttribute("aria-hidden", "true");
  frame.style.position = "fixed";
  frame.style.width = "1px";
  frame.style.height = "1px";
  frame.style.right = "0";
  frame.style.bottom = "0";
  frame.style.opacity = "0";
  frame.style.pointerEvents = "none";

  const loaded = new Promise<void>((resolve, reject) => {
    frame.addEventListener("load", () => resolve(), { once: true });
    frame.addEventListener("error", () => reject(new Error("인쇄 문서를 불러올 수 없습니다.")), { once: true });
  });

  frame.srcdoc = createPrintableHtml(bodyHtml, title);
  document.body.append(frame);

  try {
    await loaded;
    const printDocument = frame.contentDocument;
    const printWindow = frame.contentWindow;
    if (!printDocument || !printWindow) throw new Error("인쇄 창을 열 수 없습니다.");

    await printDocument.fonts?.ready;
    await waitForImages(printDocument);

    const removeFrame = () => frame.remove();
    printWindow.addEventListener("afterprint", removeFrame, { once: true });
    window.setTimeout(removeFrame, PRINT_FRAME_CLEANUP_DELAY_MS);
    printWindow.focus();
    printWindow.print();
  } catch (error) {
    frame.remove();
    throw error;
  }
}

function normalizePrintBodyHtml(bodyHtml: string): string {
  const template = document.createElement("template");
  template.innerHTML = bodyHtml;

  removeInlineLayoutStyles(template.content, "h1, h2, h3", [
    "font-size",
    "line-height",
    "margin",
    "margin-top",
    "margin-bottom",
  ]);
  removeInlineLayoutStyles(
    template.content,
    "table",
    ["font-size", "margin", "margin-top", "margin-bottom"],
  );
  removeInlineLayoutStyles(
    template.content,
    "th, td",
    ["line-height", "padding", "padding-top", "padding-right", "padding-bottom", "padding-left"],
  );

  return template.innerHTML;
}

function removeInlineLayoutStyles(root: DocumentFragment, selector: string, properties: string[]): void {
  root.querySelectorAll<HTMLElement>(selector).forEach((element) => {
    properties.forEach((property) => element.style.removeProperty(property));
    if (!element.getAttribute("style")?.trim()) element.removeAttribute("style");
  });
}

async function waitForImages(printDocument: Document): Promise<void> {
  await Promise.all(
    Array.from(printDocument.querySelectorAll("img")).map((image) => image.decode().catch(() => undefined)),
  );
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

import { createScopedContentCss } from "../styles/styles";

const PDF_PAGEBREAK_AVOID_SELECTORS = [
  ".pdf-document h1",
  ".pdf-document h2",
  ".pdf-document h3",
  ".pdf-document p",
  ".pdf-document ul",
  ".pdf-document ol",
  ".pdf-document li",
  ".pdf-document blockquote",
  ".pdf-document pre",
  ".pdf-document table",
  ".pdf-document tr",
  ".pdf-document img",
];

const PDF_EXPORT_CSS = `
${createScopedContentCss(".pdf-document")}

.pdf-document {
  box-sizing: border-box;
  width: 100%;
}

.pdf-document * {
  box-sizing: border-box;
}

.pdf-document h1 {
  margin-top: 0;
}

.pdf-document > :first-child {
  margin-top: 0 !important;
}

.pdf-document h1,
.pdf-document h2,
.pdf-document h3,
.pdf-document p,
.pdf-document ul,
.pdf-document ol,
.pdf-document li,
.pdf-document blockquote,
.pdf-document pre,
.pdf-document table,
.pdf-document tr,
.pdf-document img {
  break-inside: avoid;
  page-break-inside: avoid;
}

.pdf-document pre,
.pdf-document pre code {
  white-space: pre-wrap;
}
`.trim();

export async function downloadPdf(bodyHtml: string, title: string): Promise<void> {
  const source = createPdfSource(bodyHtml);
  const { default: html2pdf } = await import("html2pdf.js");
  const pdfOptions = {
    margin: [16, 16, 16, 16] as [number, number, number, number],
    filename: `${title}.pdf`,
    image: { type: "jpeg" as const, quality: 0.98 },
    html2canvas: {
      backgroundColor: "#ffffff",
      scale: 2,
      useCORS: true,
    },
    jsPDF: {
      unit: "mm",
      format: "a4",
      orientation: "portrait" as const,
    },
    pagebreak: {
      mode: ["css", "legacy"],
      avoid: PDF_PAGEBREAK_AVOID_SELECTORS,
    },
  };

  await html2pdf()
    .set(pdfOptions)
    .from(source)
    .save();
}

function createPdfSource(bodyHtml: string): HTMLElement {
  const source = document.createElement("div");
  const style = document.createElement("style");
  const content = document.createElement("article");

  style.textContent = PDF_EXPORT_CSS;
  content.className = "pdf-document";
  content.innerHTML = bodyHtml;

  source.append(style, content);
  return source;
}

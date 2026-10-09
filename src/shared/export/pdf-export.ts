import { createScopedContentCss } from "../styles/styles";

const DEFAULT_PDF_RENDER_SCALE = 2;
const PDF_PAGES_PER_RENDER_CHUNK = 6;

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
  const [{ default: html2pdf }, { default: html2canvas }, { jsPDF }] = await Promise.all([
    import("html2pdf.js"),
    import("html2canvas"),
    import("jspdf"),
  ]);
  const pdfOptions = {
    margin: [16, 16, 16, 16] as [number, number, number, number],
    filename: `${title}.pdf`,
    image: { type: "jpeg" as const, quality: 0.98 },
    html2canvas: {
      backgroundColor: "#ffffff",
      scale: DEFAULT_PDF_RENDER_SCALE,
      useCORS: true,
    },
    jsPDF: {
      unit: "mm" as const,
      format: "a4" as const,
      orientation: "portrait" as const,
    },
    pagebreak: {
      mode: ["css", "legacy"],
      avoid: PDF_PAGEBREAK_AVOID_SELECTORS,
    },
  };
  const worker = html2pdf().set(pdfOptions).from(source).toContainer();
  const [container, overlay, pageSize] = await Promise.all([
    worker.get("container") as Promise<HTMLElement>,
    worker.get("overlay") as Promise<HTMLElement>,
    worker.get("pageSize") as Promise<PdfPageSize>,
  ]);

  try {
    await document.fonts?.ready;
    await waitForImages(container);

    const pageWidthPx = pageSize.inner.px.width;
    const pageHeightPx = pageSize.inner.px.height;
    const chunks = createPdfChunkPlan(container.scrollHeight, pageHeightPx);
    const links = collectPdfLinks(container, pageSize);
    const pdf = new jsPDF(pdfOptions.jsPDF);
    let outputPageIndex = 0;

    for (const chunk of chunks) {
      const chunkCanvas = await html2canvas(container, {
        ...pdfOptions.html2canvas,
        width: pageWidthPx,
        height: chunk.height,
        x: 0,
        y: chunk.offset,
        windowWidth: pageWidthPx,
        windowHeight: chunk.height,
      });

      for (let pageIndex = 0; pageIndex < chunk.pageCount; pageIndex += 1) {
        const pageOffset = pageIndex * pageHeightPx;
        const pageHeight = Math.min(pageHeightPx, chunk.height - pageOffset);
        const pageCanvas = cropCanvasPage(chunkCanvas, pageWidthPx, pageOffset, pageHeight);
        const renderedHeight = (pageHeight / pageHeightPx) * pageSize.inner.height;

        if (outputPageIndex > 0) pdf.addPage();
        pdf.addImage(
          pageCanvas.toDataURL("image/jpeg", pdfOptions.image.quality),
          "JPEG",
          pdfOptions.margin[1],
          pdfOptions.margin[0],
          pageSize.inner.width,
          renderedHeight,
        );
        addPdfPageLinks(pdf, links, outputPageIndex, pdfOptions.margin);
        outputPageIndex += 1;
      }
    }

    pdf.save(pdfOptions.filename);
  } finally {
    overlay.remove();
  }
}

interface PdfPageSize {
  inner: {
    width: number;
    height: number;
    px: {
      width: number;
      height: number;
    };
  };
}

interface PdfLink {
  pageIndex: number;
  left: number;
  top: number;
  width: number;
  height: number;
  url: string;
}

export interface PdfRenderChunk {
  offset: number;
  height: number;
  pageCount: number;
}

export function createPdfChunkPlan(totalHeight: number, pageHeight: number): PdfRenderChunk[] {
  if (totalHeight <= 0 || pageHeight <= 0) return [];

  const pageCount = Math.ceil(totalHeight / pageHeight);
  const chunks: PdfRenderChunk[] = [];

  for (let firstPage = 0; firstPage < pageCount; firstPage += PDF_PAGES_PER_RENDER_CHUNK) {
    const chunkPageCount = Math.min(PDF_PAGES_PER_RENDER_CHUNK, pageCount - firstPage);
    const offset = firstPage * pageHeight;
    chunks.push({
      offset,
      height: Math.min(chunkPageCount * pageHeight, totalHeight - offset),
      pageCount: chunkPageCount,
    });
  }

  return chunks;
}

function cropCanvasPage(
  source: HTMLCanvasElement,
  pageWidth: number,
  offset: number,
  height: number,
): HTMLCanvasElement {
  const scale = source.width / pageWidth;
  const canvas = document.createElement("canvas");
  canvas.width = source.width;
  canvas.height = Math.ceil(height * scale);

  const context = canvas.getContext("2d");
  if (!context) throw new Error("PDF 페이지 캔버스를 생성할 수 없습니다.");

  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.drawImage(
    source,
    0,
    Math.floor(offset * scale),
    source.width,
    canvas.height,
    0,
    0,
    canvas.width,
    canvas.height,
  );
  return canvas;
}

async function waitForImages(container: HTMLElement): Promise<void> {
  await Promise.all(
    Array.from(container.querySelectorAll("img")).map((image) => image.decode().catch(() => undefined)),
  );
}

function collectPdfLinks(container: HTMLElement, pageSize: PdfPageSize): PdfLink[] {
  const containerRect = container.getBoundingClientRect();
  const millimetersPerPixel = pageSize.inner.width / pageSize.inner.px.width;

  return Array.from(container.querySelectorAll<HTMLAnchorElement>("a[href]")).flatMap((link) =>
    Array.from(link.getClientRects()).map((rect) => {
      const left = rect.left - containerRect.left;
      const top = rect.top - containerRect.top;
      const pageIndex = Math.floor(top / pageSize.inner.px.height);
      return {
        pageIndex,
        left: left * millimetersPerPixel,
        top: (top % pageSize.inner.px.height) * millimetersPerPixel,
        width: rect.width * millimetersPerPixel,
        height: rect.height * millimetersPerPixel,
        url: link.href,
      };
    }),
  );
}

function addPdfPageLinks(
  pdf: import("jspdf").jsPDF,
  links: PdfLink[],
  pageIndex: number,
  margin: [number, number, number, number],
): void {
  links
    .filter((link) => link.pageIndex === pageIndex)
    .forEach((link) => {
      pdf.link(margin[1] + link.left, margin[0] + link.top, link.width, link.height, {
        url: link.url,
      });
    });
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

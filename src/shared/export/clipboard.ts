export async function copyPreviewHtml(bodyHtml: string): Promise<"html" | "text"> {
  const clipboardHtml = preparePreviewHtmlForClipboard(bodyHtml);

  try {
    if ("ClipboardItem" in window && navigator.clipboard?.write) {
      const htmlBlob = new Blob([clipboardHtml], { type: "text/html" });
      const textBlob = new Blob([stripHtml(clipboardHtml)], { type: "text/plain" });
      await navigator.clipboard.write([
        new ClipboardItem({
          "text/html": htmlBlob,
          "text/plain": textBlob,
        }),
      ]);

      return "html";
    }

    return fallbackCopyHtml(clipboardHtml) ? "html" : "text";
  } catch {
    return fallbackCopyHtml(clipboardHtml) ? "html" : "text";
  }
}

export async function copyMermaidPng(svgText: string): Promise<void> {
  if (!("ClipboardItem" in window) || !navigator.clipboard?.write) {
    throw new Error("이 브라우저는 이미지 클립보드 복사를 지원하지 않습니다.");
  }

  const template = document.createElement("template");
  template.innerHTML = svgText.trim();
  const svg = template.content.querySelector("svg");
  if (!svg) throw new Error("Mermaid SVG를 찾을 수 없습니다.");

  const pngBlob = await svgToPngBlob(svg);
  await navigator.clipboard.write([
    new ClipboardItem({
      "image/png": pngBlob,
    }),
  ]);
}

export function preparePreviewHtmlForClipboard(value: string): string {
  const template = document.createElement("template");
  template.innerHTML = value;
  const diagrams = Array.from(template.content.querySelectorAll<HTMLElement>(".mermaid-diagram"));

  diagrams.forEach((diagram, index) => {
    const placeholder = document.createElement("p");
    placeholder.setAttribute("data-mermaid-placeholder", "true");
    placeholder.style.cssText = [
      "margin:24px 0",
      "padding:14px 16px",
      "border:1px dashed #9ca3af",
      "border-radius:8px",
      "background:#f9fafb",
      "color:#4b5563",
      "font-size:14px",
      "line-height:1.6",
    ].join(";");
    placeholder.textContent = `[Mermaid 다이어그램 ${index + 1} 삽입 위치 — 미리보기의 복사 아이콘으로 이미지를 별도 복사하세요]`;
    diagram.replaceWith(placeholder);
  });

  return template.innerHTML;
}

async function svgToPngBlob(svg: SVGElement): Promise<Blob> {
  const clone = svg.cloneNode(true) as SVGElement;
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  replaceForeignObjectLabels(clone);

  const viewBox = clone.getAttribute("viewBox")?.split(/\s+/).map(Number);
  const width = Math.max(1, viewBox?.[2] || Number.parseFloat(clone.getAttribute("width") ?? "") || 800);
  const height = Math.max(1, viewBox?.[3] || Number.parseFloat(clone.getAttribute("height") ?? "") || 450);
  const blob = new Blob([new XMLSerializer().serializeToString(clone)], {
    type: "image/svg+xml;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);

  try {
    const image = await loadImage(url);
    const canvas = document.createElement("canvas");
    canvas.width = Math.ceil(width * 2);
    canvas.height = Math.ceil(height * 2);
    const context = canvas.getContext("2d");
    if (!context) throw new Error("Canvas is not available.");

    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    return await canvasToPngBlob(canvas);
  } finally {
    URL.revokeObjectURL(url);
  }
}

function replaceForeignObjectLabels(svg: SVGElement): void {
  svg.querySelectorAll("foreignObject").forEach((foreignObject) => {
    const x = Number.parseFloat(foreignObject.getAttribute("x") ?? "0");
    const y = Number.parseFloat(foreignObject.getAttribute("y") ?? "0");
    const width = Number.parseFloat(foreignObject.getAttribute("width") ?? "0");
    const height = Number.parseFloat(foreignObject.getAttribute("height") ?? "0");
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");

    label.setAttribute("x", String(x + width / 2));
    label.setAttribute("y", String(y + height / 2));
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("dominant-baseline", "central");
    label.setAttribute("font-family", "Arial, sans-serif");
    label.setAttribute("font-size", "16");
    label.setAttribute("fill", "#333333");
    label.textContent = foreignObject.textContent?.trim() ?? "";
    foreignObject.replaceWith(label);
  });
}

function canvasToPngBlob(canvas: HTMLCanvasElement): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) resolve(blob);
      else reject(new Error("이미지를 만들 수 없습니다."));
    }, "image/png");
  });
}

function loadImage(source: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("SVG image could not be loaded."));
    image.src = source;
  });
}

function fallbackCopyHtml(value: string): boolean {
  const container = document.createElement("div");
  container.contentEditable = "true";
  container.innerHTML = value;
  container.style.cssText = "position:fixed;left:-9999px;top:0;";
  document.body.append(container);

  const selection = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(container);
  selection?.removeAllRanges();
  selection?.addRange(range);

  const copied = document.execCommand("copy");
  selection?.removeAllRanges();
  container.remove();
  return copied;
}

function stripHtml(value: string): string {
  const template = document.createElement("template");
  template.innerHTML = value;
  return template.content.textContent?.trim() ?? "";
}

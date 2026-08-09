import type { PreviewStyle } from "../../shared/markdown/types";

export function buildPreviewHtml(fullHtml: string, previewStyle: PreviewStyle): string {
  const previewHtml = injectMermaidCopyControls(fullHtml);

  if (previewStyle === "compact") {
    return previewHtml.replaceAll("max-width: 800px;", "max-width: 660px;");
  }

  if (previewStyle === "editor") {
    return previewHtml.replace(
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

  return previewHtml;
}

function injectMermaidCopyControls(fullHtml: string): string {
  const controls = `
<style>
.mermaid-diagram {
  position: relative;
  padding-top: 42px;
}

.mermaid-copy-button {
  position: absolute;
  top: 0;
  right: 0;
  display: grid;
  width: 34px;
  height: 34px;
  padding: 0;
  place-items: center;
  border: 1px solid #d1d5db;
  border-radius: 7px;
  background: #fff;
  color: #374151;
  cursor: pointer;
}

.mermaid-copy-button svg {
  width: 17px;
  height: 17px;
}

.mermaid-copy-button:hover {
  border-color: #9ca3af;
  background: #f9fafb;
}
</style>
<script>
document.querySelectorAll('.mermaid-diagram').forEach(function (diagram) {
  var svg = diagram.querySelector('svg');
  if (!svg) return;

  var button = document.createElement('button');
  button.type = 'button';
  button.className = 'mermaid-copy-button';
  button.title = 'PNG 이미지 복사';
  button.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="9" y="9" width="11" height="11" rx="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>';
  button.setAttribute('aria-label', 'Mermaid 다이어그램 PNG 이미지 복사');
  button.addEventListener('click', function () {
    window.parent.postMessage({ type: 'copy-mermaid-png', svg: svg.outerHTML }, '*');
  });
  diagram.prepend(button);
});
</script>`;

  return fullHtml.replace("</body>", `${controls}\n</body>`);
}

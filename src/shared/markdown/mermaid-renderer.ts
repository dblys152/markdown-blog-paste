type MermaidApi = typeof import("mermaid")["default"];

let diagramSequence = 0;
let mermaidPromise: Promise<MermaidApi> | null = null;

function loadMermaid(): Promise<MermaidApi> {
  if (!mermaidPromise) {
    mermaidPromise = import("mermaid").then(({ default: mermaid }) => {
      mermaid.initialize({
        startOnLoad: false,
        securityLevel: "strict",
        theme: "default",
        flowchart: {
          htmlLabels: false,
        },
      });
      return mermaid;
    });
  }

  return mermaidPromise;
}

interface PendingDiagram {
  placeholder: HTMLElement;
  originalCodeBlock: HTMLPreElement;
  source: string;
}

export async function renderMermaidDiagrams(
  htmlText: string,
  onProgress?: (html: string) => void,
): Promise<string> {
  const template = document.createElement("template");
  template.innerHTML = htmlText;

  const codeBlocks = Array.from(
    template.content.querySelectorAll<HTMLElement>("pre > code.language-mermaid"),
  );

  if (codeBlocks.length === 0) return htmlText;

  const pendingDiagrams = codeBlocks.flatMap<PendingDiagram>((codeBlock) => {
    const pre = codeBlock.parentElement;
    if (!(pre instanceof HTMLPreElement)) return [];

    const placeholder = document.createElement("figure");
    placeholder.className = "mermaid-diagram is-loading";
    placeholder.setAttribute("aria-label", "Mermaid 다이어그램 준비 중");
    pre.replaceWith(placeholder);

    return [{
      placeholder,
      originalCodeBlock: pre,
      source: codeBlock.textContent?.replace(/\n$/, "") ?? "",
    }];
  });

  onProgress?.(template.innerHTML);
  const mermaid = await loadMermaid();

  await Promise.all(
    pendingDiagrams.map(async ({ placeholder, originalCodeBlock, source }) => {
      try {
        const id = `md2blog-mermaid-${Date.now()}-${diagramSequence++}`;
        const { svg } = await mermaid.render(id, source);
        placeholder.classList.remove("is-loading");
        placeholder.removeAttribute("aria-label");
        placeholder.innerHTML = svg;
        placeholder.querySelector("svg")?.setAttribute("role", "img");
      } catch {
        originalCodeBlock.classList.add("mermaid-error");
        originalCodeBlock.setAttribute("title", "Mermaid 다이어그램을 렌더링할 수 없습니다.");
        placeholder.replaceWith(originalCodeBlock);
      }

      onProgress?.(template.innerHTML);
    }),
  );

  return template.innerHTML;
}

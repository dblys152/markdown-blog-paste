import mermaid from "mermaid";

let diagramSequence = 0;

mermaid.initialize({
  startOnLoad: false,
  securityLevel: "strict",
  theme: "default",
  flowchart: {
    htmlLabels: false,
  },
});

export async function renderMermaidDiagrams(htmlText: string): Promise<string> {
  const template = document.createElement("template");
  template.innerHTML = htmlText;

  const codeBlocks = Array.from(
    template.content.querySelectorAll<HTMLElement>("pre > code.language-mermaid"),
  );

  await Promise.all(
    codeBlocks.map(async (codeBlock) => {
      const pre = codeBlock.parentElement;
      if (!pre) return;

      const source = codeBlock.textContent?.replace(/\n$/, "") ?? "";
      const container = document.createElement("figure");
      container.className = "mermaid-diagram";

      try {
        const id = `md2blog-mermaid-${Date.now()}-${diagramSequence++}`;
        const { svg } = await mermaid.render(id, source);
        container.innerHTML = svg;
        container.querySelector("svg")?.setAttribute("role", "img");
        pre.replaceWith(container);
      } catch {
        pre.classList.add("mermaid-error");
        pre.setAttribute("title", "Mermaid 다이어그램을 렌더링할 수 없습니다.");
      }
    }),
  );

  return template.innerHTML;
}

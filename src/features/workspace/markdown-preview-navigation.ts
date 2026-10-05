export function bindMarkdownPreviewNavigation(document: Document): void {
  const targets = document.querySelectorAll<HTMLElement>("[data-section-target]");

  targets.forEach((target) => {
    target.addEventListener("click", (event) => {
      const id = target.dataset.sectionTarget;
      const heading = id ? document.getElementById(id) : null;
      if (!heading) return;

      event.preventDefault();
      heading.scrollIntoView({ behavior: "smooth", block: "start" });
      targets.forEach((item) => item.classList.toggle("is-active", item.dataset.sectionTarget === id));
    });
  });
}

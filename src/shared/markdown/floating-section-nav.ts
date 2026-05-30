import type { TocEntry } from "./types";

export function renderFloatingSectionNav(entries: TocEntry[]): string {
  if (entries.length === 0) {
    return "";
  }

  return `
    <aside class="floating-section-nav" aria-label="섹션 내비게이션" data-floating-section-nav>
      <nav class="floating-section-nav-bars" aria-label="섹션 바로가기">
        ${entries.map(renderTocBar).join("")}
      </nav>
      <div class="floating-section-nav-panel" role="navigation" aria-label="문서 목차">
        <div class="floating-section-nav-title">목차</div>
        <div class="floating-section-nav-list">
          ${entries.map(renderTocLink).join("")}
        </div>
      </div>
    </aside>
    <script>
${FLOATING_SECTION_NAV_SCRIPT}
    </script>
  `;
}

function renderTocBar(entry: TocEntry): string {
  return `<button class="floating-section-nav-bar toc-level-${entry.level}" type="button" data-section-target="${escapeAttribute(
    entry.id,
  )}" aria-label="${escapeAttribute(entry.text)}"></button>`;
}

function renderTocLink(entry: TocEntry): string {
  return `<a class="floating-section-nav-link toc-level-${entry.level}" href="#${escapeAttribute(
    entry.id,
  )}" data-section-target="${escapeAttribute(entry.id)}">${escapeHtml(entry.text)}</a>`;
}

function escapeAttribute(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

const FLOATING_SECTION_NAV_SCRIPT = `(() => {
  const nav = document.querySelector("[data-floating-section-nav]");

  if (!nav || !("IntersectionObserver" in window)) {
    return;
  }

  const targets = Array.from(nav.querySelectorAll("[data-section-target]"));
  const ids = Array.from(new Set(targets.map((target) => target.getAttribute("data-section-target")).filter(Boolean)));
  const headings = ids.map((id) => document.getElementById(id)).filter(Boolean);
  let activeId = "";

  const getOffset = () => {
    const value = getComputedStyle(document.documentElement).getPropertyValue("--section-scroll-offset").trim();
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : 24;
  };

  const setActive = (id) => {
    if (!id || activeId === id) {
      return;
    }

    activeId = id;
    targets.forEach((target) => {
      target.classList.toggle("is-active", target.getAttribute("data-section-target") === id);
    });
  };

  nav.querySelectorAll(".floating-section-nav-link[data-section-target]").forEach((target) => {
    target.addEventListener("click", (event) => {
      const id = target.getAttribute("data-section-target");
      const heading = id ? document.getElementById(id) : null;

      if (!heading) {
        return;
      }

      event.preventDefault();
      const top = heading.getBoundingClientRect().top + window.scrollY - getOffset();

      try {
        window.history.pushState(null, "", "#" + id);
      } catch {
        // Sandboxed previews can block history updates. Scrolling should still work.
      }

      window.scrollTo({ top, behavior: "smooth" });
      setActive(id);
      target.blur();
    });
  });

  const hashId = window.location.hash ? decodeURIComponent(window.location.hash.slice(1)) : "";
  setActive(ids.includes(hashId) ? hashId : ids[0]);

  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => Math.abs(a.boundingClientRect.top) - Math.abs(b.boundingClientRect.top));

      if (visible[0]?.target.id) {
        setActive(visible[0].target.id);
      }
    },
    {
      rootMargin: "-20% 0px -65% 0px",
      threshold: [0, 1],
    },
  );

  headings.forEach((heading) => observer.observe(heading));
})();`;

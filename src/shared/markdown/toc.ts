import type { TocEntry } from "./types";

interface TocResult {
  bodyHtml: string;
  entries: TocEntry[];
}

export function addHeadingAnchors(bodyHtml: string): TocResult {
  const template = document.createElement("template");
  const usedIds = new Map<string, number>();
  const entries: TocEntry[] = [];

  template.innerHTML = bodyHtml;

  template.content.querySelectorAll("h2, h3, [data-section-nav][id]").forEach((heading) => {
    const text = heading.textContent?.trim();

    if (!text) {
      return;
    }

    const existingId = heading.getAttribute("id")?.trim();
    const id = existingId || createUniqueHeadingId(text, usedIds);
    const headingLevel = Number(heading.tagName.slice(1));
    const level = headingLevel === 2 || headingLevel === 3 ? headingLevel : 2;

    heading.setAttribute("id", id);
    entries.push({ id, level, text });
  });

  return {
    bodyHtml: template.innerHTML,
    entries,
  };
}

function createUniqueHeadingId(text: string, usedIds: Map<string, number>): string {
  const baseId = slugify(text) || "section";
  const count = usedIds.get(baseId) ?? 0;

  usedIds.set(baseId, count + 1);

  if (count === 0) {
    return baseId;
  }

  return `${baseId}-${count + 1}`;
}

function slugify(value: string): string {
  return value
    .normalize("NFKD")
    .toLowerCase()
    .replace(/[^\p{Letter}\p{Number}]+/gu, "-")
    .replace(/^-+|-+$/g, "");
}

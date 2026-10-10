import { type CSSProperties, useMemo, useState } from "react";
import type { WorkspacePageListItem } from "../../features/workspace/api";
import { PageTypeIcon } from "../../features/workspace/page-type-presentation";

interface WorkspaceSaveTargetPickerProps {
  pages: WorkspacePageListItem[];
  value: string;
  onChange: (value: string) => void;
}

interface PageOption {
  page: WorkspacePageListItem;
  depth: number;
  path: string;
}

function buildPageOptions(pages: WorkspacePageListItem[]): PageOption[] {
  const childrenByParent = new Map<string | null, WorkspacePageListItem[]>();
  const pageIds = new Set(pages.map((page) => page.id));
  pages.forEach((page) => {
    const parentId = page.parent_id !== null && pageIds.has(page.parent_id) ? page.parent_id : null;
    const children = childrenByParent.get(parentId) ?? [];
    children.push(page);
    childrenByParent.set(parentId, children);
  });
  childrenByParent.forEach((children) => children.sort((left, right) => (
    left.sort_order - right.sort_order || left.id.localeCompare(right.id)
  )));

  const options: PageOption[] = [];
  const visit = (parentId: string | null, depth: number, parentPath: string[]) => {
    (childrenByParent.get(parentId) ?? []).forEach((page) => {
      const path = [...parentPath, page.title];
      options.push({ page, depth, path: path.join(" › ") });
      visit(page.id, depth + 1, path);
    });
  };
  visit(null, 0, []);
  return options;
}

export function WorkspaceSaveTargetPicker({ pages, value, onChange }: WorkspaceSaveTargetPickerProps) {
  const [query, setQuery] = useState("");
  const options = useMemo(() => buildPageOptions(pages), [pages]);
  const normalizedQuery = query.trim().toLocaleLowerCase("ko-KR");
  const visibleOptions = normalizedQuery
    ? options.filter(({ page, path }) => (
      page.title.toLocaleLowerCase("ko-KR").includes(normalizedQuery)
      || path.toLocaleLowerCase("ko-KR").includes(normalizedQuery)
    ))
    : options;

  return (
    <div className="workspace-save-picker">
      <div className="workspace-save-picker-panel">
        <label className="workspace-save-picker-search">
          <span aria-hidden="true">⌕</span>
          <input
            type="search"
            aria-label="저장 대상 페이지 검색"
            placeholder="페이지 검색"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
        <div className="workspace-save-picker-options" role="listbox" aria-label="저장 대상">
            <button
              type="button"
              role="option"
              aria-selected={value === "new"}
              className={value === "new" ? "is-selected" : ""}
              onClick={() => onChange("new")}
            >
              <span className="workspace-save-picker-new-icon" aria-hidden="true">+</span>
              <span><strong>새 Markdown 페이지 만들기</strong><small>기록장 최상위에 새 페이지를 만듭니다.</small></span>
              {value === "new" && <span className="workspace-save-picker-check" aria-hidden="true">✓</span>}
            </button>
            {visibleOptions.map(({ page, depth, path }) => {
              const isMarkdown = (page.type ?? "MARKDOWN") === "MARKDOWN";
              const isSelected = page.id === value;
              return (
                <button
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  aria-disabled={!isMarkdown}
                  disabled={!isMarkdown}
                  className={`${isSelected ? "is-selected" : ""}${depth > 0 ? " has-depth" : ""}`}
                  key={page.id}
                  style={{ "--save-target-indent": `${Math.min(depth, 6) * 18}px` } as CSSProperties}
                  onClick={() => onChange(page.id)}
                >
                  <span className={`workspace-save-picker-type is-${(page.type ?? "MARKDOWN").toLowerCase()}`}>
                    <PageTypeIcon pageType={page.type} className="workspace-save-picker-type-icon" />
                  </span>
                  <span><strong>{page.title}</strong><small>{path}</small></span>
                  {isSelected && <span className="workspace-save-picker-check" aria-hidden="true">✓</span>}
                </button>
              );
            })}
            {visibleOptions.length === 0 && <p>일치하는 페이지가 없습니다.</p>}
        </div>
      </div>
    </div>
  );
}

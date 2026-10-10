import type { PageType } from "./api";

export const PAGE_TYPE_OPTIONS: readonly PageType[] = ["MARKDOWN", "MEMO", "HTML", "PDF"];

export function pageTypeName(pageType: PageType): string {
  if (pageType === "MARKDOWN") return "Markdown";
  if (pageType === "MEMO") return "메모";
  return pageType;
}

export function pageTypeDescription(pageType: PageType): string {
  if (pageType === "PDF") return "보관 및 열람";
  if (pageType === "MEMO") return "미리보기 없이 작성";
  return "작성 및 미리보기";
}

export function pageTypeDocumentLabel(pageType: PageType): string {
  return pageType === "MEMO" ? "메모 문서" : `${pageTypeName(pageType)} 문서`;
}

interface PageTypeIconProps {
  pageType?: PageType;
  className: string;
  accessible?: boolean;
}

export function PageTypeIcon({ pageType = "MARKDOWN", className, accessible = false }: PageTypeIconProps) {
  return (
    <svg
      className={`${className} is-${pageType.toLowerCase()}`}
      viewBox="0 0 20 20"
      fill="none"
      role={accessible ? "img" : undefined}
      aria-label={accessible ? pageTypeDocumentLabel(pageType) : undefined}
      aria-hidden={accessible ? undefined : true}
    >
      {pageType === "MEMO" ? (
        <>
          <path d="M3.5 3.5h9l4 4v9h-13z" />
          <path d="M12.5 3.5v4h4" />
        </>
      ) : (
        <>
          <path d="M3.5 2.5h9l4 4v11h-13z" />
          <path d="M12.5 2.5v4h4" />
          {pageType === "HTML" && <path d="m8 9-2.5 2 2.5 2M12 9l2.5 2-2.5 2" />}
          {pageType === "PDF" && <text className="workspace-page-type-text is-pdf" x="10" y="13.5">PDF</text>}
          {pageType === "MARKDOWN" && <text className="workspace-page-type-text is-markdown" x="10" y="13.5">MD</text>}
        </>
      )}
    </svg>
  );
}

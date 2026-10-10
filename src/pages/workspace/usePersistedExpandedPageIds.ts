import { type Dispatch, type SetStateAction, useCallback, useEffect, useMemo, useState } from "react";

type PageTreeScope = "pages" | "trash";

const STORAGE_KEY_PREFIX = "md2blog.workspace.expanded-page-ids";

function loadExpandedPageIds(storageKey: string | null): Set<string> {
  if (storageKey === null) return new Set();
  try {
    const storedValue: unknown = JSON.parse(window.localStorage.getItem(storageKey) ?? "[]");
    if (!Array.isArray(storedValue)) return new Set();
    return new Set(storedValue.filter((value): value is string => typeof value === "string"));
  } catch {
    return new Set();
  }
}

function saveExpandedPageIds(storageKey: string | null, pageIds: Set<string>): void {
  if (storageKey === null) return;
  try {
    window.localStorage.setItem(storageKey, JSON.stringify([...pageIds]));
  } catch {
    // 저장소 접근이 제한되어도 현재 화면의 펼침 상태는 유지합니다.
  }
}

export function usePersistedExpandedPageIds(
  userId: string | undefined,
  scope: PageTreeScope,
): [Set<string>, Dispatch<SetStateAction<Set<string>>>] {
  const storageKey = useMemo(
    () => userId ? `${STORAGE_KEY_PREFIX}.${userId}.${scope}` : null,
    [scope, userId],
  );
  const [expandedPageIds, setExpandedPageIdsState] = useState(() => loadExpandedPageIds(storageKey));

  useEffect(() => {
    setExpandedPageIdsState(loadExpandedPageIds(storageKey));
  }, [storageKey]);

  const setExpandedPageIds = useCallback<Dispatch<SetStateAction<Set<string>>>>((value) => {
    setExpandedPageIdsState((current) => {
      const next = typeof value === "function" ? value(current) : value;
      saveExpandedPageIds(storageKey, next);
      return next;
    });
  }, [storageKey]);

  return [expandedPageIds, setExpandedPageIds];
}

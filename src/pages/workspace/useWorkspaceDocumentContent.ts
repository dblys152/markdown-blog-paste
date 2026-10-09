import { type Dispatch, type SetStateAction, useCallback, useEffect, useRef, useState } from "react";
import {
  getWorkspacePage,
  updateWorkspacePage,
  type PageType,
  type WorkspacePageListItem,
} from "../../features/workspace/api";
import { measureAsync } from "../../shared/performance/measureAsync";

export type WorkspaceSaveState = "loading" | "saving" | "saved" | "error";

interface WorkspaceDocumentContentOptions {
  initialContent: string;
  autosaveEnabled: boolean;
  selectedPageId: string | null;
  pageType: PageType;
  title: string;
  setPages: Dispatch<SetStateAction<WorkspacePageListItem[]>>;
  onLoadError: () => void;
}

export function useWorkspaceDocumentContent({
  initialContent,
  autosaveEnabled,
  selectedPageId,
  pageType,
  title,
  setPages,
  onLoadError,
}: WorkspaceDocumentContentOptions) {
  const [content, setContent] = useState(initialContent);
  const [saveState, setSaveState] = useState<WorkspaceSaveState>("loading");
  const contentCache = useRef(new Map<string, string>());
  const pendingContentRequests = useRef(new Map<string, Promise<string>>());
  const hydrated = useRef(false);
  const skipNextSave = useRef(false);
  const requestId = useRef(0);

  useEffect(() => () => {
    requestId.current += 1;
    pendingContentRequests.current.clear();
  }, []);

  const fetchPageContent = useCallback((pageId: string, useCache = true): Promise<string> => {
    if (useCache) {
      const cachedContent = contentCache.current.get(pageId);
      if (cachedContent !== undefined) return Promise.resolve(cachedContent);
    }

    const pendingRequest = pendingContentRequests.current.get(pageId);
    if (pendingRequest) return pendingRequest;

    const request = measureAsync("md2blog.workspace.page-detail", async () => {
      const detail = await getWorkspacePage(pageId);
      const pageContent = detail.contents ?? "";
      contentCache.current.set(detail.id, pageContent);
      return pageContent;
    }).finally(() => {
      pendingContentRequests.current.delete(pageId);
    });
    pendingContentRequests.current.set(pageId, request);
    return request;
  }, []);

  useEffect(() => {
    if (!autosaveEnabled || !hydrated.current || !selectedPageId) return;
    if (skipNextSave.current) {
      skipNextSave.current = false;
      return;
    }
    if (!title.trim()) {
      setSaveState("error");
      return;
    }

    setSaveState("saving");
    const timer = window.setTimeout(() => {
      updateWorkspacePage(
        selectedPageId,
        pageType === "PDF" ? { title } : { title, content },
      )
        .then((updatedPage) => {
          contentCache.current.set(updatedPage.id, updatedPage.contents ?? "");
          setPages((current) => current.map((page) => page.id === updatedPage.id ? updatedPage : page));
          setSaveState("saved");
        })
        .catch(() => setSaveState("error"));
    }, 600);
    return () => window.clearTimeout(timer);
  }, [autosaveEnabled, content, pageType, selectedPageId, setPages, title]);

  const loadPageContent = useCallback(async (
    page: WorkspacePageListItem,
    options: { useCache?: boolean } = {},
  ) => {
    const currentRequestId = ++requestId.current;
    skipNextSave.current = true;
    hydrated.current = false;

    if (options.useCache !== false) {
      const cachedContent = contentCache.current.get(page.id);
      if (cachedContent !== undefined) {
        setContent(cachedContent);
        hydrated.current = true;
        setSaveState("saved");
        return;
      }
    }

    setSaveState("loading");
    setContent("");
    try {
      const pageContent = await fetchPageContent(page.id, options.useCache !== false);
      if (requestId.current !== currentRequestId) return;
      setContent(pageContent);
      hydrated.current = true;
      setSaveState("saved");
    } catch {
      if (requestId.current !== currentRequestId) return;
      setSaveState("error");
      onLoadError();
    }
  }, [fetchPageContent, onLoadError]);

  const prefetchPageContent = useCallback((page: WorkspacePageListItem) => {
    if (page.type === "PDF" || contentCache.current.has(page.id)) return;
    void fetchPageContent(page.id).catch(() => {
      // 선로딩 실패는 실제 페이지 선택 시 다시 시도합니다.
    });
  }, [fetchPageContent]);

  const initializeEmptyContent = useCallback(() => {
    requestId.current += 1;
    setContent("");
    skipNextSave.current = true;
    hydrated.current = true;
    setSaveState("saved");
  }, []);

  const suspendAutosave = useCallback(() => {
    requestId.current += 1;
    hydrated.current = false;
  }, []);

  const cachePageContent = useCallback((pageId: string, pageContent: string | null | undefined) => {
    contentCache.current.set(pageId, pageContent ?? "");
  }, []);

  const removeCachedContent = useCallback((pageIds: Iterable<string>) => {
    for (const pageId of pageIds) contentCache.current.delete(pageId);
  }, []);

  const preventNextSave = useCallback(() => {
    skipNextSave.current = true;
  }, []);

  return {
    content,
    setContent,
    saveState,
    setSaveState,
    loadPageContent,
    prefetchPageContent,
    initializeEmptyContent,
    suspendAutosave,
    cachePageContent,
    removeCachedContent,
    preventNextSave,
  };
}

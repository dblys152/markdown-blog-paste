import { useEffect, useRef, useState } from "react";
import {
  getWorkspacePdfBlob,
  getWorkspacePdfUrl,
  type PageType,
} from "../../features/workspace/api";

interface WorkspacePdfPreviewOptions {
  pageId: string | null;
  pageType: PageType;
  onError: () => void;
}

interface PdfCacheEntry {
  url: string;
  isObjectUrl: boolean;
  size: number;
  expiresAt: number;
  lastUsedAt: number;
}

interface PdfPreviewState {
  pageId: string | null;
  url: string;
}

const MAX_CACHED_PDFS = 3;
const MAX_CACHED_PDF_BYTES = 50 * 1024 * 1024;
const SIGNED_URL_EXPIRY_MARGIN_MS = 30_000;

function isUsable(entry: PdfCacheEntry): boolean {
  return entry.expiresAt > Date.now() + SIGNED_URL_EXPIRY_MARGIN_MS;
}

function revokeEntry(entry: PdfCacheEntry): void {
  if (entry.isObjectUrl) URL.revokeObjectURL(entry.url);
}

export function useWorkspacePdfPreview({ pageId, pageType, onError }: WorkspacePdfPreviewOptions): string {
  const [preview, setPreview] = useState<PdfPreviewState>({ pageId: null, url: "" });
  const cache = useRef(new Map<string, PdfCacheEntry>());
  const pendingRequests = useRef(new Map<string, Promise<PdfCacheEntry>>());
  const mounted = useRef(true);
  const activePageId = useRef(pageId);
  activePageId.current = pageId;

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      pendingRequests.current.clear();
      cache.current.forEach(revokeEntry);
      cache.current.clear();
    };
  }, []);

  useEffect(() => {
    if (!pageId || pageType !== "PDF") {
      setPreview({ pageId: null, url: "" });
      return;
    }

    const cachedEntry = cache.current.get(pageId);
    if (cachedEntry && isUsable(cachedEntry)) {
      cachedEntry.lastUsedAt = Date.now();
      setPreview({ pageId, url: cachedEntry.url });
      return;
    }
    if (cachedEntry) {
      revokeEntry(cachedEntry);
      cache.current.delete(pageId);
    }

    let cancelled = false;
    setPreview({ pageId, url: "" });

    const loadPdf = async (): Promise<PdfCacheEntry> => {
      const { url, expires_in: expiresIn } = await getWorkspacePdfUrl(pageId);
      if (!url.startsWith("/")) {
        const expiresInSeconds = Number(expiresIn);
        return {
          url,
          isObjectUrl: false,
          size: 0,
          expiresAt: Number.isFinite(expiresInSeconds) ? Date.now() + expiresInSeconds * 1000 : Date.now(),
          lastUsedAt: Date.now(),
        };
      }

      const blob = await getWorkspacePdfBlob(url);
      if (!mounted.current) throw new Error("PDF preview unmounted");
      return {
        url: URL.createObjectURL(blob),
        isObjectUrl: true,
        size: blob.size,
        expiresAt: Number.POSITIVE_INFINITY,
        lastUsedAt: Date.now(),
      };
    };

    let request = pendingRequests.current.get(pageId);
    if (!request) {
      request = loadPdf().then((entry) => {
        cache.current.set(pageId, entry);
        let totalBytes = [...cache.current.values()].reduce((total, cached) => total + cached.size, 0);
        while (cache.current.size > MAX_CACHED_PDFS || totalBytes > MAX_CACHED_PDF_BYTES) {
          const oldest = [...cache.current.entries()]
            .filter(([cachedPageId]) => cachedPageId !== activePageId.current)
            .sort(([, left], [, right]) => left.lastUsedAt - right.lastUsedAt)[0];
          if (!oldest) break;
          cache.current.delete(oldest[0]);
          totalBytes -= oldest[1].size;
          revokeEntry(oldest[1]);
        }
        return entry;
      }).finally(() => pendingRequests.current.delete(pageId));
      pendingRequests.current.set(pageId, request);
    }

    request
      .then((entry) => {
        if (!cancelled) setPreview({ pageId, url: entry.url });
      })
      .catch(() => {
        if (!cancelled) onError();
      });

    return () => {
      cancelled = true;
    };
  }, [onError, pageId, pageType]);

  return preview.pageId === pageId ? preview.url : "";
}

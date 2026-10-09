import { useEffect, useState } from "react";
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

export function useWorkspacePdfPreview({ pageId, pageType, onError }: WorkspacePdfPreviewOptions): string {
  const [pdfUrl, setPdfUrl] = useState("");

  useEffect(() => {
    if (!pageId || pageType !== "PDF") {
      setPdfUrl("");
      return;
    }

    let cancelled = false;
    let objectUrl = "";
    getWorkspacePdfUrl(pageId)
      .then(async ({ url }) => {
        if (!url.startsWith("/")) return url;
        const blob = await getWorkspacePdfBlob(url);
        objectUrl = URL.createObjectURL(blob);
        return objectUrl;
      })
      .then((url) => {
        if (!cancelled) setPdfUrl(url);
      })
      .catch(() => {
        if (!cancelled) onError();
      });

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [onError, pageId, pageType]);

  return pdfUrl;
}

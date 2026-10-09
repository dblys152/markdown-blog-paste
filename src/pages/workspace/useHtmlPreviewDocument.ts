import { useEffect, useState } from "react";
import { buildHtmlPreviewDocument } from "../../features/workspace/html-preview";

interface HtmlPreviewState {
  documentKey: string;
  document: string;
}

const HTML_PREVIEW_DEBOUNCE_MS = 250;

export function useHtmlPreviewDocument(source: string, documentKey: string, enabled: boolean): string {
  const [preview, setPreview] = useState<HtmlPreviewState | null>(null);

  useEffect(() => {
    if (!enabled) {
      setPreview(null);
      return;
    }

    const timer = window.setTimeout(() => {
      setPreview({
        documentKey,
        document: buildHtmlPreviewDocument(source),
      });
    }, HTML_PREVIEW_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [documentKey, enabled, source]);

  return enabled && preview?.documentKey === documentKey ? preview.document : "";
}

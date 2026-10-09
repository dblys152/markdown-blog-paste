import { useEffect, useState } from "react";
import { convertMarkdown } from "../../shared/markdown/converter-core";
import type { ConversionResult } from "../../shared/markdown/types";
import { measureAsync } from "../../shared/performance/measureAsync";

export function useMarkdownConversion(markdown: string, title: string, enabled = true) {
  const [result, setResult] = useState<ConversionResult | null>(null);
  const [isConverting, setIsConverting] = useState(true);

  useEffect(() => {
    if (!enabled) {
      setResult(null);
      setIsConverting(false);
      return;
    }

    let cancelled = false;
    setIsConverting(true);
    measureAsync("md2blog.workspace.markdown-conversion", () => (
      convertMarkdown(markdown, "basic", title, undefined, (partialResult) => {
        if (!cancelled) setResult(partialResult);
      })
    )).then((convertedResult) => {
      if (cancelled) return;
      setResult(convertedResult);
      setIsConverting(false);
    });
    return () => {
      cancelled = true;
    };
  }, [enabled, markdown, title]);

  return { result, isConverting };
}

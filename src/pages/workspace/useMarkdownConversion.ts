import { useEffect, useState } from "react";
import { convertMarkdown } from "../../shared/markdown/converter-core";
import type { ConversionResult } from "../../shared/markdown/types";

export function useMarkdownConversion(markdown: string, title: string) {
  const [result, setResult] = useState<ConversionResult | null>(null);
  const [isConverting, setIsConverting] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setIsConverting(true);
    convertMarkdown(markdown, "basic", title, undefined, (partialResult) => {
      if (!cancelled) setResult(partialResult);
    }).then((convertedResult) => {
      if (cancelled) return;
      setResult(convertedResult);
      setIsConverting(false);
    });
    return () => {
      cancelled = true;
    };
  }, [markdown, title]);

  return { result, isConverting };
}

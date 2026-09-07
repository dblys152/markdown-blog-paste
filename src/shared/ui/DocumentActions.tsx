import { useEffect, useRef, useState } from "react";
import type { ConversionResult } from "../markdown/types";
import { copyPreviewHtml } from "../export/clipboard";
import { downloadHtml } from "../export/html-export";
import { downloadMarkdown } from "../export/markdown-export";
import { downloadPdf } from "../export/pdf-export";

interface DocumentActionsProps {
  result: ConversionResult | null;
  markdown: string;
  title: string;
  onMessage: (message: string) => void;
  onSave?: () => void | Promise<void>;
}

export function DocumentActions({ result, markdown, title, onMessage, onSave }: DocumentActionsProps) {
  const [isExportOpen, setIsExportOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isExportOpen) return;

    const closeOnOutsidePointer = (event: PointerEvent) => {
      const target = event.target;
      if (!(target instanceof Node) || !menuRef.current?.contains(target)) {
        setIsExportOpen(false);
      }
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsExportOpen(false);
    };
    const closeOnWindowBlur = () => setIsExportOpen(false);

    document.addEventListener("pointerdown", closeOnOutsidePointer);
    document.addEventListener("keydown", closeOnEscape);
    window.addEventListener("blur", closeOnWindowBlur);
    return () => {
      document.removeEventListener("pointerdown", closeOnOutsidePointer);
      document.removeEventListener("keydown", closeOnEscape);
      window.removeEventListener("blur", closeOnWindowBlur);
    };
  }, [isExportOpen]);

  const handleCopy = async () => {
    if (!result) return;
    const copiedType = await copyPreviewHtml(result.bodyHtml);
    onMessage(copiedType === "html" ? "미리보기 HTML을 클립보드에 복사했습니다." : "미리보기 HTML을 텍스트로 복사했습니다.");
  };

  const handlePdf = async () => {
    if (!result) return;
    try {
      setIsExportOpen(false);
      onMessage("PDF 파일을 생성하고 있습니다.");
      await downloadPdf(result.bodyHtml, title);
      onMessage("PDF 파일 다운로드를 시작했습니다.");
    } catch {
      onMessage("PDF 파일을 만들 수 없습니다.");
    }
  };

  return (
    <div className="document-actions">
      <button type="button" disabled={!result} onClick={() => void handleCopy()}>
        <span aria-hidden="true">⧉</span><span>미리보기 내용 복사</span>
      </button>
      <div className="document-export" ref={menuRef}>
        <button type="button" aria-haspopup="menu" aria-expanded={isExportOpen} disabled={!result} onClick={() => setIsExportOpen((open) => !open)}>
          <span aria-hidden="true">⇩</span><span>내보내기</span>
        </button>
        {isExportOpen && (
          <div className="document-export-menu" role="menu">
            <button type="button" role="menuitem" onClick={() => {
              if (!result) return;
              setIsExportOpen(false);
              downloadHtml(result.fullHtml, title);
              onMessage("HTML 파일 다운로드를 시작했습니다.");
            }}><span aria-hidden="true">&lt;/&gt;</span><span><strong>HTML 다운로드</strong><small>브라우저에서 열 수 있는 문서</small></span></button>
            <button type="button" role="menuitem" onClick={() => void handlePdf()}><span aria-hidden="true">▤</span><span><strong>PDF 다운로드</strong><small>공유하기 좋은 문서 파일</small></span></button>
            <button type="button" role="menuitem" onClick={() => {
              setIsExportOpen(false);
              downloadMarkdown(markdown, title);
              onMessage("Markdown 파일 다운로드를 시작했습니다.");
            }}><span aria-hidden="true">#</span><span><strong>Markdown 다운로드</strong><small>원본 Markdown 문서</small></span></button>
          </div>
        )}
      </div>
      {onSave && (
        <button className="document-save-button" type="button" onClick={() => void onSave()}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M6 3h12a1 1 0 0 1 1 1v17l-7-4-7 4V4a1 1 0 0 1 1-1Z" />
          </svg>
          <span>기록장에 저장</span>
        </button>
      )}
    </div>
  );
}

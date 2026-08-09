import type { ConversionMode, UploadedMarkdownFile } from "../../shared/markdown/types";

const STORAGE_KEY = "md2blog-quick-conversion-draft";

export interface QuickConversionDraft {
  markdownText: string;
  currentFile: UploadedMarkdownFile;
  mode: ConversionMode;
  excludeFirstH1: boolean;
  generateH2Toc: boolean;
  addH2Dividers: boolean;
}

interface StoredQuickConversionDraft extends Omit<QuickConversionDraft, "currentFile"> {
  currentFile: Omit<UploadedMarkdownFile, "text">;
}

let memoryDraft: QuickConversionDraft | null = null;

export function loadQuickConversionDraft(): QuickConversionDraft | null {
  if (memoryDraft) return memoryDraft;

  try {
    const stored = window.sessionStorage.getItem(STORAGE_KEY);
    if (!stored) return null;
    const storedDraft = JSON.parse(stored) as Partial<StoredQuickConversionDraft>;
    if (
      typeof storedDraft.markdownText !== "string"
      || typeof storedDraft.currentFile?.name !== "string"
      || typeof storedDraft.currentFile.size !== "number"
    ) return null;

    const draft: QuickConversionDraft = {
      markdownText: storedDraft.markdownText,
      currentFile: {
        name: storedDraft.currentFile.name,
        size: storedDraft.currentFile.size,
        isSample: storedDraft.currentFile.isSample === true,
        text: storedDraft.markdownText,
      },
      mode: isConversionMode(storedDraft.mode) ? storedDraft.mode : "basic",
      excludeFirstH1: storedDraft.excludeFirstH1 === true,
      generateH2Toc: storedDraft.generateH2Toc === true,
      addH2Dividers: storedDraft.addH2Dividers === true,
    };
    memoryDraft = draft;
    return draft;
  } catch {
    return null;
  }
}

export function saveQuickConversionDraft(draft: QuickConversionDraft): void {
  memoryDraft = draft;
  try {
    const storedDraft: StoredQuickConversionDraft = {
      ...draft,
      currentFile: {
        name: draft.currentFile.name,
        size: draft.currentFile.size,
        isSample: draft.currentFile.isSample,
      },
    };
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(storedDraft));
  } catch {
    // 큰 파일로 세션 저장소 한도를 넘더라도 SPA 화면 이동 중에는 메모리 복원을 유지합니다.
  }
}

function isConversionMode(value: unknown): value is ConversionMode {
  return value === "basic" || value === "blank-lines" || value === "naver";
}

export function clearQuickConversionDraft(): void {
  memoryDraft = null;
  try {
    window.sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // 테스트나 제한된 브라우저 환경에서 저장소를 사용할 수 없어도 메모리 상태는 초기화합니다.
  }
}

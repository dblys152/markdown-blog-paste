import { beforeEach, describe, expect, it } from "vitest";
import {
  clearQuickConversionDraft,
  loadQuickConversionDraft,
  saveQuickConversionDraft,
} from "../../../src/pages/markdown-paste/quick-conversion-draft-store";

const STORAGE_KEY = "md2blog-quick-conversion-draft";

describe("quick-conversion-draft-store", () => {
  beforeEach(() => clearQuickConversionDraft());

  it("Markdown 본문을 파일 정보에 중복 저장하지 않는다", () => {
    saveQuickConversionDraft({
      markdownText: "# 저장할 본문",
      currentFile: { name: "post.md", size: 12, text: "# 저장할 본문", isSample: false },
      mode: "basic",
      excludeFirstH1: false,
      generateH2Toc: false,
      addH2Dividers: false,
    });

    const stored = JSON.parse(window.sessionStorage.getItem(STORAGE_KEY) ?? "{}") as {
      markdownText?: string;
      currentFile?: { text?: string };
    };
    expect(stored.markdownText).toBe("# 저장할 본문");
    expect(stored.currentFile?.text).toBeUndefined();
  });

  it("손상된 세션 데이터는 복원하지 않는다", () => {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ markdownText: 123, currentFile: null }));

    expect(loadQuickConversionDraft()).toBeNull();
  });
});

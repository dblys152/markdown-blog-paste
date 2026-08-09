export type ConversionMode = "basic" | "blank-lines" | "naver";

export type PreviewStyle = "default" | "compact" | "editor";

export interface ConversionOptions {
  excludeFirstH1: boolean;
  generateH2Toc: boolean;
  addH2Dividers: boolean;
}

export interface UploadedMarkdownFile {
  name: string;
  size: number;
  text: string;
  isSample?: boolean;
}

export interface ConversionResult {
  bodyHtml: string;
  fullHtml: string;
}

export interface ModeOption {
  id: ConversionMode;
  title: string;
  description: string;
}

export interface TocEntry {
  id: string;
  level: 1 | 2 | 3;
  text: string;
}

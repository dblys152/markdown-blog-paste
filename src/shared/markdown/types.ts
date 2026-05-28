export type ConversionMode = "basic" | "blank-lines" | "naver";

export type PreviewStyle = "default" | "compact" | "editor";

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

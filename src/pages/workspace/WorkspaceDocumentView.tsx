import type { KeyboardEvent, PointerEvent } from "react";
import type { PageType } from "../../features/workspace/api";
import { pageTypeName } from "../../features/workspace/page-type-presentation";
import { bindMarkdownPreviewNavigation } from "../../features/workspace/markdown-preview-navigation";
import { downloadHtml } from "../../shared/export/html-export";
import type { ConversionResult } from "../../shared/markdown/types";
import { DocumentActions } from "../../shared/ui/DocumentActions";

type SaveState = "loading" | "saving" | "saved" | "error";

interface WorkspaceDocumentViewProps {
  pageType: PageType;
  title: string;
  pdfUrl: string;
  content: string;
  result: ConversionResult | null;
  isConverting: boolean;
  htmlPreviewDocument: string;
  editableTitle: string | null;
  saveState: SaveState;
  isAuthenticated: boolean;
  editorReadOnly: boolean;
  editorDisabled: boolean;
  editorRatio: number;
  onTitleChange: (title: string) => void;
  onContentChange: (content: string) => void;
  onMessage: (message: string) => void;
  onDividerPointerDown: (event: PointerEvent<HTMLDivElement>) => void;
  onDividerPointerMove: (event: PointerEvent<HTMLDivElement>) => void;
  onDividerPointerUp: (event: PointerEvent<HTMLDivElement>) => void;
  onDividerPointerCancel: (event: PointerEvent<HTMLDivElement>) => void;
  onDividerLostPointerCapture: () => void;
  onDividerKeyDown: (event: KeyboardEvent<HTMLDivElement>) => void;
  onDividerReset: () => void;
}

type EditorPaneProps = Pick<
  WorkspaceDocumentViewProps,
  | "title"
  | "content"
  | "editableTitle"
  | "saveState"
  | "isAuthenticated"
  | "editorReadOnly"
  | "editorDisabled"
  | "onTitleChange"
  | "onContentChange"
> & {
  pageType: Exclude<PageType, "PDF">;
  documentTypeLabel: string;
};

type PreviewPaneProps = Pick<
  WorkspaceDocumentViewProps,
  | "title"
  | "content"
  | "result"
  | "isConverting"
  | "htmlPreviewDocument"
  | "editorRatio"
  | "onMessage"
  | "onDividerPointerDown"
  | "onDividerPointerMove"
  | "onDividerPointerUp"
  | "onDividerPointerCancel"
  | "onDividerLostPointerCapture"
  | "onDividerKeyDown"
  | "onDividerReset"
> & { pageType: "MARKDOWN" | "HTML" };

export function WorkspaceDocumentView(props: WorkspaceDocumentViewProps) {
  if (props.pageType === "PDF") {
    return <PdfDocumentView title={props.title} pdfUrl={props.pdfUrl} />;
  }

  return <TextDocumentView {...props} pageType={props.pageType} />;
}

function PdfDocumentView({ title, pdfUrl }: { title: string; pdfUrl: string }) {
  return (
    <section className="workspace-preview workspace-pdf-viewer" aria-label="PDF Viewer">
      <div className="workspace-preview-heading">
        <strong>PDF Viewer</strong>
        <span className="workspace-external-resource-note">원본 PDF · 최대 20MB</span>
      </div>
      {pdfUrl
        ? <iframe title={`${title} PDF`} src={pdfUrl} />
        : <div className="workspace-empty-state">PDF를 불러오는 중입니다.</div>}
    </section>
  );
}

function TextDocumentView(props: WorkspaceDocumentViewProps & { pageType: Exclude<PageType, "PDF"> }) {
  const documentTypeLabel = pageTypeName(props.pageType);

  if (props.pageType === "MEMO") {
    return <EditorPane {...props} documentTypeLabel={documentTypeLabel} />;
  }

  return <>
    <EditorPane {...props} documentTypeLabel={documentTypeLabel} />
    <PreviewPane {...props} pageType={props.pageType} />
  </>;
}

function EditorPane({
  pageType,
  title,
  content,
  editableTitle,
  saveState,
  isAuthenticated,
  editorReadOnly,
  editorDisabled,
  onTitleChange,
  onContentChange,
  documentTypeLabel,
}: EditorPaneProps) {
  const lineCount = content.split("\n").length;

  return (
    <section className={`workspace-editor${pageType === "MEMO" ? " is-memo-editor" : ""}`} aria-label={`${documentTypeLabel} 편집기`}>
      <div className="workspace-editor-heading">
        <div><span aria-hidden="true">✎</span><strong>{documentTypeLabel}</strong></div>
        <div className="workspace-document-state">
          {editableTitle !== null ? (
            <input
              className="workspace-document-title-input"
              aria-label="페이지 제목"
              value={editableTitle}
              maxLength={200}
              onChange={(event) => onTitleChange(event.target.value)}
            />
          ) : <span className="workspace-document-title">{title}</span>}
          <span aria-hidden="true">·</span>
          <span className={`workspace-save-label save-${saveState}`}>
            {saveState === "loading" && "불러오는 중"}
            {saveState === "saving" && "저장 중…"}
            {saveState === "saved" && (isAuthenticated ? "✓ 저장됨" : "✓ 브라우저에 저장됨")}
            {saveState === "error" && "저장 실패"}
          </span>
        </div>
      </div>
      <div className="workspace-code-area">
        <div className="workspace-line-numbers" aria-hidden="true">
          {Array.from({ length: Math.max(lineCount, 32) }, (_, index) => <span key={index}>{index + 1}</span>)}
        </div>
        <textarea
          aria-label={`${documentTypeLabel} 내용`}
          spellCheck={false}
          value={content}
          onChange={(event) => onContentChange(event.target.value)}
          readOnly={editorReadOnly}
          disabled={editorDisabled}
        />
      </div>
      <footer className="workspace-statusbar">
        <span>줄 1, 열 1</span><span>{documentTypeLabel}</span><span>{content.length.toLocaleString("ko-KR")}자</span>
      </footer>
    </section>
  );
}

function PreviewPane({
  pageType,
  title,
  content,
  result,
  isConverting,
  htmlPreviewDocument,
  editorRatio,
  onMessage,
  onDividerPointerDown,
  onDividerPointerMove,
  onDividerPointerUp,
  onDividerPointerCancel,
  onDividerLostPointerCapture,
  onDividerKeyDown,
  onDividerReset,
}: PreviewPaneProps) {
  return <>
    <div
      className="workspace-divider"
      role="separator"
      aria-label="에디터와 미리보기 너비 조절"
      aria-orientation="vertical"
      aria-valuemin={28}
      aria-valuemax={72}
      aria-valuenow={Math.round(editorRatio * 100)}
      tabIndex={0}
      onPointerDown={onDividerPointerDown}
      onPointerMove={onDividerPointerMove}
      onPointerUp={onDividerPointerUp}
      onPointerCancel={onDividerPointerCancel}
      onLostPointerCapture={onDividerLostPointerCapture}
      onKeyDown={onDividerKeyDown}
      onDoubleClick={onDividerReset}
    ><span aria-hidden="true">⠿</span></div>

    <section className={`workspace-preview${pageType === "HTML" ? " is-html-preview" : ""}`} aria-labelledby="workspace-preview-title">
      <div className="workspace-preview-heading">
        <strong id="workspace-preview-title">미리보기</strong>
        {pageType === "MARKDOWN" && (
          <DocumentActions
            result={isConverting ? null : result}
            markdown={content}
            title={title}
            onMessage={onMessage}
          />
        )}
        {pageType === "HTML" && (
          <div className="document-actions">
            <button type="button" onClick={() => {
              downloadHtml(content, title);
              onMessage("HTML 파일 다운로드를 시작했습니다.");
            }}>
              <span aria-hidden="true">⇩</span><span>HTML 내보내기</span>
            </button>
          </div>
        )}
      </div>
      {pageType === "HTML" && (
        <p className="workspace-external-resource-note">
          외부 이미지를 불러오면 이미지 서버에 현재 사용자의 IP가 전달될 수 있습니다.
        </p>
      )}
      <iframe
        title={`${title} 미리보기`}
        sandbox={pageType === "MARKDOWN" ? "allow-same-origin" : ""}
        referrerPolicy="no-referrer"
        srcDoc={pageType === "HTML" ? htmlPreviewDocument : (result?.fullHtml ?? "")}
        onLoad={(event) => {
          if (pageType === "MARKDOWN" && event.currentTarget.contentDocument) {
            bindMarkdownPreviewNavigation(event.currentTarget.contentDocument);
          }
        }}
      />
      <footer className="workspace-statusbar is-preview"><span>{content.length.toLocaleString("ko-KR")}자</span><span>미리보기</span></footer>
    </section>
  </>;
}

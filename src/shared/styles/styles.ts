export const BASE_CSS = `
:root {
  --section-scroll-offset: 24px;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  background: #fff;
  color: #222;
  font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
}

.document-layout {
  max-width: 800px;
  margin: 40px auto;
  padding: 0 20px;
}

.document-content {
  min-width: 0;
}

${createContentRootCss(".document-content")}

${createContentCss(".document-content")}

.document-content h1,
.document-content h2,
.document-content h3 {
  scroll-margin-top: var(--section-scroll-offset);
}

.floating-section-nav {
  position: fixed;
  top: 50%;
  right: 24px;
  z-index: 20;
  display: grid;
  justify-items: end;
  transform: translateY(-50%);
}

.floating-section-nav-bars {
  display: grid;
  gap: 8px;
  justify-items: end;
  padding: 8px 0;
}

.floating-section-nav-bar {
  display: block;
  width: 20px;
  height: 3px;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: #c7cdd5;
  opacity: 0.75;
  cursor: pointer;
  transition: width 140ms ease, background 140ms ease, opacity 140ms ease;
}

.floating-section-nav-bar.toc-level-3 {
  width: 13px;
}

.floating-section-nav-bar:hover,
.floating-section-nav-bar.is-active {
  width: 28px;
  background: #111827;
  opacity: 1;
}

.floating-section-nav-panel {
  position: absolute;
  top: 50%;
  right: 0;
  width: min(260px, calc(100vw - 96px));
  max-height: min(420px, calc(100vh - 48px));
  overflow: auto;
  padding: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.16);
  opacity: 0;
  pointer-events: none;
  transform: translateY(-50%) translateX(8px);
  transition: opacity 140ms ease, transform 140ms ease;
}

.floating-section-nav:hover .floating-section-nav-panel,
.floating-section-nav:focus-within .floating-section-nav-panel {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(-50%) translateX(0);
}

.floating-section-nav-title {
  margin-bottom: 10px;
  color: #111827;
  font-size: 13px;
  font-weight: 800;
  line-height: 1.3;
}

.floating-section-nav-list {
  display: grid;
  gap: 5px;
}

.floating-section-nav-link {
  display: block;
  padding: 5px 6px;
  border-radius: 6px;
  color: #5d6673;
  font-size: 13px;
  line-height: 1.35;
  text-decoration: none;
  transition: background 140ms ease, color 140ms ease;
}

.floating-section-nav-link:hover,
.floating-section-nav-link.is-active {
  background: #f3f4f6;
  color: #111827;
}

.floating-section-nav-link.toc-level-3 {
  padding-left: 18px;
  font-size: 12px;
}

@media (max-width: 640px) {
  .floating-section-nav {
    display: none;
  }
}
`.trim();

export function createScopedContentCss(scope: string): string {
  return `
${createContentRootCss(scope)}

${createContentCss(scope)}
`.trim();
}

function createContentRootCss(
  selector: string,
  layout: { maxWidth?: string; margin?: string; padding?: string } = {},
): string {
  const layoutRules = [
    layout.maxWidth ? `  max-width: ${layout.maxWidth};` : "",
    layout.margin ? `  margin: ${layout.margin};` : "",
    layout.padding ? `  padding: ${layout.padding};` : "",
  ].filter(Boolean);

  return `
${selector} {
  font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
  line-height: 1.9;
  font-size: 16px;
  color: #222;
  background: #fff;
${layoutRules.join("\n")}
}
`.trim();
}

function createContentCss(scope = ""): string {
  const selector = (value: string) =>
    value
      .split(",")
      .map((part) => `${scope ? `${scope} ` : ""}${part.trim()}`)
      .join(",\n");

  return `
${selector("h1")} {
  font-size: 28px;
  margin-top: 44px;
  margin-bottom: 24px;
  line-height: 1.4;
}

${selector("h2")} {
  font-size: 24px;
  margin-top: 44px;
  margin-bottom: 20px;
  line-height: 1.4;
}

${selector("h3")} {
  font-size: 19px;
  margin-top: 36px;
  margin-bottom: 16px;
  line-height: 1.5;
}

${selector("p")} {
  margin: 16px 0;
  line-height: 1.9;
}

${selector("ul, ol")} {
  margin: 16px 0;
  padding-left: 28px;
}

${selector("li")} {
  margin: 8px 0;
  line-height: 1.8;
}

${selector("blockquote")} {
  margin: 24px 0;
  padding: 14px 18px;
  border-left: 4px solid #d1d5db;
  background: #f9fafb;
  color: #555;
}

${selector("pre")} {
  display: block;
  background: #f8f9fa;
  color: #111827;
  padding: 18px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  overflow-x: auto;
  line-height: 1.75;
  font-size: 15px;
  white-space: pre;
  margin: 24px 0;
}

${selector("pre code")} {
  display: block;
  background: transparent;
  color: #111827;
  font-family: Consolas, Monaco, "Courier New", monospace;
  font-size: 15px;
  line-height: 1.75;
  white-space: pre;
}

${selector("code")} {
  font-family: Consolas, Monaco, "Courier New", monospace;
}

${selector("p code, li code")} {
  background: #f3f4f6;
  color: #d6336c;
  padding: 2px 5px;
  border-radius: 4px;
  font-size: 0.9em;
}

${selector("table")} {
  border-collapse: collapse;
  width: 100%;
  margin: 24px 0;
  font-size: 15px;
}

${selector("th, td")} {
  border: 1px solid #ddd;
  padding: 10px 12px;
  line-height: 1.7;
}

${selector("th")} {
  background: #f5f5f5;
  font-weight: 700;
}

${selector("hr")} {
  border: 0;
  border-top: 1px solid #e5e7eb;
  margin: 36px 0;
}

${selector(".editor-spacer")} {
  font-size: 16px;
  line-height: 1.4;
  margin: 0;
}

${selector("img")} {
  max-width: 100%;
}
`.trim();
}

export const APP_CSS = `
:root {
  color: #111827;
  background: #f6f7f9;
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

* {
  box-sizing: border-box;
}

html,
body,
#app {
  min-height: 100%;
}

body {
  margin: 0;
}

button,
input,
select,
textarea {
  font: inherit;
}

button {
  border: 0;
}

.app-shell {
  min-height: 100vh;
  padding: 22px 24px 24px;
  background:
    radial-gradient(circle at 15% 0%, rgba(255, 255, 255, 0.9), transparent 28%),
    linear-gradient(180deg, #fbfcfd 0%, #f3f5f7 100%);
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 28px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.brand-mark-button {
  display: inline-flex;
  width: 46px;
  height: 46px;
  padding: 0;
  border: 0;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
}

.brand-mark {
  display: block;
  width: 46px;
  height: 46px;
  border-radius: 8px;
  box-shadow: 0 12px 26px rgba(17, 18, 19, 0.18);
}

.brand h1 {
  margin: 0;
  font-size: 28px;
  line-height: 1.1;
  letter-spacing: 0;
}

.brand-title-button {
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
}

.brand p {
  margin: 7px 0 0;
  color: #5d6673;
  font-size: 14px;
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-button,
.secondary-button,
.primary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 40px;
  border-radius: 8px;
  border: 1px solid #d8dde5;
  background: #fff;
  color: #111827;
  cursor: pointer;
  transition: border-color 140ms ease, box-shadow 140ms ease, background 140ms ease, transform 140ms ease;
}

.secondary-button,
.primary-button {
  width: 100%;
  padding: 0 16px;
  font-weight: 700;
}

.primary-button {
  border-color: #111213;
  background: #111213;
  color: #fff;
}

.icon-button {
  width: 40px;
  color: #0f1115;
  text-decoration: none;
}

.button-small {
  width: auto;
  min-height: 34px;
  padding: 0 12px;
  font-size: 13px;
}

button:hover {
  border-color: #9aa3af;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
}

button:active {
  transform: translateY(1px);
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
  box-shadow: none;
}

.layout {
  display: grid;
  grid-template-columns: minmax(300px, 368px) minmax(0, 1fr);
  gap: 28px;
  align-items: stretch;
}

.panel {
  border: 1px solid #dfe4ea;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
}

.settings-panel {
  padding: 24px;
}

.panel h2 {
  margin: 0 0 24px;
  font-size: 21px;
  line-height: 1.2;
}

.section {
  padding-bottom: 24px;
  margin-bottom: 24px;
  border-bottom: 1px solid #dfe4ea;
}

.section:last-child {
  padding-bottom: 0;
  margin-bottom: 0;
  border-bottom: 0;
}

.section-title {
  margin: 0 0 14px;
  font-size: 16px;
  font-weight: 800;
}

.dropzone {
  display: grid;
  place-items: center;
  min-height: 116px;
  padding: 20px;
  border: 1px solid #cdd4dd;
  border-radius: 8px;
  background: #fafbfc;
  text-align: center;
  transition: border-color 140ms ease, background 140ms ease;
}

.dropzone.is-dragging {
  border-color: #111213;
  background: #eef2f6;
}

.dropzone p {
  margin: 10px 0 14px;
  color: #374151;
  font-size: 14px;
}

.file-input {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
}

.file-chip {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 12px;
  align-items: center;
  margin-top: 12px;
  color: #111827;
  font-size: 13px;
}

.file-name {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  gap: 8px;
}

.file-name span:last-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.success-dot {
  width: 13px;
  height: 13px;
  border-radius: 999px;
  background: #22c55e;
  box-shadow: inset 0 0 0 3px rgba(255, 255, 255, 0.65);
}

.remove-file {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: transparent;
  color: #4b5563;
}

.mode-list {
  display: grid;
  gap: 14px;
}

.mode-option {
  display: grid;
  grid-template-columns: 20px 1fr;
  gap: 10px;
  align-items: start;
  cursor: pointer;
}

.mode-option input {
  width: 18px;
  height: 18px;
  margin: 1px 0 0;
  accent-color: #111213;
}

.mode-option strong {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
}

.mode-option span {
  color: #5d6673;
  font-size: 13px;
  line-height: 1.55;
}

.action-stack {
  display: grid;
  gap: 10px;
}

.tip {
  margin-top: 24px;
  padding: 16px;
  border: 1px solid #f1d889;
  border-radius: 8px;
  background: #fff9e8;
  color: #765a13;
  font-size: 13px;
  line-height: 1.65;
}

.tip-title {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 6px;
  color: #b7791f;
}

.tip p {
  margin: 0;
}

.preview-panel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-height: calc(100vh - 144px);
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 18px 24px;
}

.preview-title {
  margin: 0;
  font-size: 21px;
}

.preview-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #374151;
  font-size: 14px;
}

.preview-controls label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.preview-controls select {
  min-width: 148px;
  height: 36px;
  padding: 0 36px 0 12px;
  border: 1px solid #d8dde5;
  border-radius: 8px;
  background: #fff;
  color: #111827;
}

.preview-wrap {
  min-height: 0;
  margin: 0 24px 8px;
  border: 1px solid #d8dde5;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

.preview-frame {
  width: 100%;
  height: 100%;
  min-height: calc(100vh - 230px);
  border: 0;
  background: #fff;
}

.toast {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 10;
  max-width: min(360px, calc(100vw - 48px));
  padding: 12px 14px;
  border-radius: 8px;
  background: #111213;
  color: #fff;
  font-size: 14px;
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.22);
}

.empty-state {
  display: grid;
  place-items: center;
  min-height: 360px;
  color: #6b7280;
  text-align: center;
}

@media (max-width: 920px) {
  .app-shell {
    padding: 18px;
  }

  .topbar {
    align-items: flex-start;
  }

  .layout {
    grid-template-columns: 1fr;
  }

  .preview-panel {
    min-height: 640px;
  }

  .preview-frame {
    min-height: 520px;
  }
}

@media (max-width: 620px) {
  .preview-header {
    flex-direction: column;
    align-items: stretch;
  }

  .topbar {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: start;
    gap: 12px;
  }

  .brand {
    align-items: flex-start;
  }

  .brand h1 {
    font-size: 24px;
  }

  .top-actions {
    gap: 8px;
    justify-content: flex-end;
  }

  .settings-panel,
  .preview-header {
    padding: 18px;
  }

  .preview-wrap {
    margin: 0 18px 8px;
  }

  .preview-controls {
    justify-content: space-between;
  }
}
`;

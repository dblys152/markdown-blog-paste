const HTML_PREVIEW_CSP = [
  "default-src 'none'",
  "img-src https: data: blob:",
  "style-src 'unsafe-inline'",
  "font-src data:",
].join("; ");

export function buildHtmlPreviewDocument(source: string): string {
  const document = new DOMParser().parseFromString(source, "text/html");
  const policy = document.createElement("meta");
  policy.httpEquiv = "Content-Security-Policy";
  policy.content = HTML_PREVIEW_CSP;
  document.head.prepend(policy);
  return `<!doctype html>\n${document.documentElement.outerHTML}`;
}

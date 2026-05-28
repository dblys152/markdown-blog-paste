export async function copyPreviewHtml(bodyHtml: string): Promise<"html" | "text"> {
  try {
    if ("ClipboardItem" in window && navigator.clipboard?.write) {
      const htmlBlob = new Blob([bodyHtml], { type: "text/html" });
      const textBlob = new Blob([stripHtml(bodyHtml)], { type: "text/plain" });
      await navigator.clipboard.write([
        new ClipboardItem({
          "text/html": htmlBlob,
          "text/plain": textBlob,
        }),
      ]);

      return "html";
    }

    await navigator.clipboard.writeText(bodyHtml);
    return "text";
  } catch {
    fallbackCopy(bodyHtml);
    return "text";
  }
}

function fallbackCopy(value: string): void {
  const textarea = document.createElement("textarea");
  textarea.value = value;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  document.body.append(textarea);
  textarea.select();
  document.execCommand("copy");
  textarea.remove();
}

function stripHtml(value: string): string {
  const template = document.createElement("template");
  template.innerHTML = value;
  return template.content.textContent?.trim() ?? "";
}

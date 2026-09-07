import { useCallback, useEffect, useRef, useState } from "react";

export type ConfirmDialogOptions = {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: "default" | "danger";
};

export function useConfirmDialog() {
  const [options, setOptions] = useState<ConfirmDialogOptions | null>(null);
  const resolverRef = useRef<((confirmed: boolean) => void) | null>(null);

  const close = useCallback((confirmed: boolean) => {
    resolverRef.current?.(confirmed);
    resolverRef.current = null;
    setOptions(null);
  }, []);

  const requestConfirmation = useCallback((nextOptions: ConfirmDialogOptions) => {
    resolverRef.current?.(false);
    setOptions(nextOptions);
    return new Promise<boolean>((resolve) => {
      resolverRef.current = resolve;
    });
  }, []);

  useEffect(() => () => resolverRef.current?.(false), []);

  const confirmationDialog = options ? (
    <div
      className="confirm-dialog-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) close(false);
      }}
    >
      <section
        className={`confirm-dialog ${options.tone === "danger" ? "is-danger" : ""}`}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-message"
        onKeyDown={(event) => {
          if (event.key === "Escape") close(false);
        }}
      >
        <div className="confirm-dialog-icon" aria-hidden="true">
          {options.tone === "danger" ? "!" : "?"}
        </div>
        <div className="confirm-dialog-content">
          <h2 id="confirm-dialog-title">{options.title}</h2>
          <p id="confirm-dialog-message">{options.message}</p>
        </div>
        <div className="confirm-dialog-actions">
          <button type="button" onClick={() => close(false)} autoFocus>
            {options.cancelLabel ?? "취소"}
          </button>
          <button
            type="button"
            className={options.tone === "danger" ? "is-danger" : "is-primary"}
            onClick={() => close(true)}
          >
            {options.confirmLabel ?? "확인"}
          </button>
        </div>
      </section>
    </div>
  ) : null;

  return { requestConfirmation, confirmationDialog };
}

export function createToast(root: HTMLElement): (message: string) => void {
  let toastTimer: number | undefined;

  return (message: string) => {
    window.clearTimeout(toastTimer);
    root.querySelector(".toast")?.remove();

    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    root.append(toast);

    toastTimer = window.setTimeout(() => toast.remove(), 2600);
  };
}

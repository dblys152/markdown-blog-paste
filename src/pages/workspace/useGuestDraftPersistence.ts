import { type Dispatch, type SetStateAction, useEffect, useRef } from "react";
import { loadGuestDraft, saveGuestDraft } from "./guest-draft-store";

type SaveState = "loading" | "saving" | "saved" | "error";

interface GuestDraftPersistenceOptions {
  enabled: boolean;
  title: string;
  markdown: string;
  onMarkdownLoaded: (markdown: string) => void;
  setSaveState: Dispatch<SetStateAction<SaveState>>;
}

export function useGuestDraftPersistence({
  enabled,
  title,
  markdown,
  onMarkdownLoaded,
  setSaveState,
}: GuestDraftPersistenceOptions): void {
  const hydrated = useRef(false);

  useEffect(() => {
    if (!enabled) return;

    loadGuestDraft()
      .then(async (draft) => {
        if (draft?.markdown) onMarkdownLoaded(draft.markdown);
        if (draft && draft.title !== title) {
          await saveGuestDraft({ ...draft, title, updatedAt: Date.now() });
        }
      })
      .catch(() => setSaveState("error"))
      .finally(() => {
        hydrated.current = true;
        setSaveState((current) => (current === "error" ? current : "saved"));
      });
  }, [enabled]);

  useEffect(() => {
    if (!enabled || !hydrated.current) return;

    setSaveState("saving");
    const timer = window.setTimeout(() => {
      saveGuestDraft({ title, markdown, updatedAt: Date.now() })
        .then(() => setSaveState("saved"))
        .catch(() => setSaveState("error"));
    }, 450);
    return () => window.clearTimeout(timer);
  }, [enabled, markdown, title]);
}

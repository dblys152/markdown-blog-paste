import { useEffect, useRef, useState } from "react";
import { GOOGLE_CLIENT_ID } from "../../shared/config/env";

type CredentialResponse = { credential?: string };

type GoogleAccounts = {
  id: {
    initialize: (options: { client_id: string; callback: (response: CredentialResponse) => void }) => void;
    renderButton: (element: HTMLElement, options: Record<string, string | number>) => void;
  };
};

declare global {
  interface Window {
    google?: { accounts: GoogleAccounts };
  }
}

let googleScriptPromise: Promise<void> | null = null;

function loadGoogleIdentityScript(): Promise<void> {
  if (window.google?.accounts) return Promise.resolve();
  if (googleScriptPromise) return googleScriptPromise;

  googleScriptPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>('script[src="https://accounts.google.com/gsi/client"]');
    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error("Google 로그인 화면을 불러오지 못했습니다.")), { once: true });
      return;
    }
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Google 로그인 화면을 불러오지 못했습니다."));
    document.head.append(script);
  });
  return googleScriptPromise;
}

type Props = {
  onCredential: (credential: string) => void | Promise<void>;
  text?: "signin_with" | "continue_with";
  disabled?: boolean;
};

export function GoogleIdentityButton({ onCredential, text = "continue_with", disabled = false }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const callbackRef = useRef(onCredential);
  const [error, setError] = useState<string | null>(null);
  callbackRef.current = onCredential;

  useEffect(() => {
    const clientId = GOOGLE_CLIENT_ID;
    if (!clientId || disabled) return;
    let active = true;
    void loadGoogleIdentityScript()
      .then(() => {
        if (!active || !containerRef.current || !window.google) return;
        containerRef.current.replaceChildren();
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: (response) => {
            if (response.credential) void callbackRef.current(response.credential);
          },
        });
        window.google.accounts.id.renderButton(containerRef.current, {
          type: "standard",
          theme: "outline",
          size: "large",
          shape: "rectangular",
          text,
          width: Math.min(388, containerRef.current.clientWidth || 388),
          locale: "ko",
        });
      })
      .catch((loadError: unknown) => {
        if (active) setError(loadError instanceof Error ? loadError.message : "Google 로그인을 사용할 수 없습니다.");
      });
    return () => { active = false; };
  }, [disabled, text]);

  if (!GOOGLE_CLIENT_ID) {
    return <p className="google-auth-unavailable">Google 로그인을 사용하려면 Client ID 설정이 필요합니다.</p>;
  }
  return (
    <div className={disabled ? "google-identity-button is-disabled" : "google-identity-button"}>
      <div ref={containerRef} />
      {error && <p className="auth-error" role="alert">{error}</p>}
    </div>
  );
}

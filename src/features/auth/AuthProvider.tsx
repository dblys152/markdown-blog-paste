import { createContext, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  login as loginRequest,
  logout as logoutRequest,
  restoreSession,
  signup as signupRequest,
  type AuthUser,
  type LoginInput,
  type SignupInput,
} from "./api";

type AuthStatus = "loading" | "guest" | "authenticated";

type AuthContextValue = {
  status: AuthStatus;
  user: AuthUser | null;
  login: (input: LoginInput) => Promise<void>;
  signup: (input: SignupInput) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<AuthUser | null>(null);
  const bootstrapStarted = useRef(false);

  useEffect(() => {
    if (bootstrapStarted.current) return;
    bootstrapStarted.current = true;

    void restoreSession().then((session) => {
      setUser(session?.user ?? null);
      setStatus(session ? "authenticated" : "guest");
    });
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      login: async (input) => {
        const session = await loginRequest(input);
        setUser(session.user);
        setStatus("authenticated");
      },
      signup: async (input) => {
        const session = await signupRequest(input);
        setUser(session.user);
        setStatus("authenticated");
      },
      logout: async () => {
        try {
          await logoutRequest();
        } finally {
          setUser(null);
          setStatus("guest");
        }
      },
    }),
    [status, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth는 AuthProvider 안에서 사용해야 합니다.");
  }
  return context;
}

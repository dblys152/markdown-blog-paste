import { createContext, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  confirmEmailVerification as confirmEmailVerificationRequest,
  deleteAccount as deleteAccountRequest,
  deleteGoogleAccount as deleteGoogleAccountRequest,
  googleLogin as googleLoginRequest,
  googleSignup as googleSignupRequest,
  linkGoogleAndLogin as linkGoogleAndLoginRequest,
  login as loginRequest,
  logout as logoutRequest,
  requestEmailVerification as requestEmailVerificationRequest,
  restoreSession,
  signup as signupRequest,
  updateDisplayName as updateDisplayNameRequest,
  type AuthUser,
  type GoogleLoginFlow,
  type LoginInput,
  type SignupInput,
} from "./api";

type AuthStatus = "loading" | "guest" | "authenticated";

type AuthContextValue = {
  status: AuthStatus;
  user: AuthUser | null;
  login: (input: LoginInput) => Promise<void>;
  signup: (input: SignupInput) => Promise<void>;
  googleLogin: (credential: string) => Promise<GoogleLoginFlow>;
  googleSignup: (credential: string, displayName: string) => Promise<void>;
  linkGoogleAndLogin: (credential: string, password: string) => Promise<void>;
  requestEmailVerification: () => Promise<void>;
  confirmEmailVerification: (token: string) => Promise<AuthUser>;
  refreshCurrentUser: () => Promise<AuthUser | null>;
  deleteAccount: (password: string) => Promise<void>;
  deleteGoogleAccount: (credential: string) => Promise<void>;
  updateDisplayName: (displayName: string) => Promise<AuthUser>;
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
      googleLogin: async (credential) => {
        const result = await googleLoginRequest(credential);
        if ("access_token" in result) {
          setUser(result.user);
          setStatus("authenticated");
        }
        return result;
      },
      googleSignup: async (credential, displayName) => {
        const session = await googleSignupRequest(credential, displayName);
        setUser(session.user);
        setStatus("authenticated");
      },
      linkGoogleAndLogin: async (credential, password) => {
        const session = await linkGoogleAndLoginRequest(credential, password);
        setUser(session.user);
        setStatus("authenticated");
      },
      requestEmailVerification: requestEmailVerificationRequest,
      confirmEmailVerification: async (token) => {
        const verifiedUser = await confirmEmailVerificationRequest(token);
        if (status === "authenticated") {
          setUser(verifiedUser);
        }
        return verifiedUser;
      },
      refreshCurrentUser: async () => {
        const session = await restoreSession();
        setUser(session?.user ?? null);
        setStatus(session ? "authenticated" : "guest");
        return session?.user ?? null;
      },
      deleteAccount: async (password) => {
        await deleteAccountRequest(password);
        setUser(null);
        setStatus("guest");
      },
      deleteGoogleAccount: async (credential) => {
        await deleteGoogleAccountRequest(credential);
        setUser(null);
        setStatus("guest");
      },
      updateDisplayName: async (displayName) => {
        const updatedUser = await updateDisplayNameRequest(displayName);
        setUser(updatedUser);
        return updatedUser;
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

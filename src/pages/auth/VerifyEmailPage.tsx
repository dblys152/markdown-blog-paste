import { useEffect, useRef, useState } from "react";
import { Link, Navigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../../features/auth/AuthProvider";
import { ApiError } from "../../shared/api/http";

type VerificationState = "waiting" | "confirming" | "verified" | "error";

export function VerifyEmailPage() {
  const {
    status,
    user,
    requestEmailVerification,
    confirmEmailVerification,
    refreshCurrentUser,
  } = useAuth();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const confirmationStarted = useRef(false);
  const [verificationState, setVerificationState] = useState<VerificationState>(token ? "confirming" : "waiting");
  const [message, setMessage] = useState<string | null>(null);
  const [isResending, setIsResending] = useState(false);

  useEffect(() => {
    if (!token || confirmationStarted.current) return;
    confirmationStarted.current = true;
    void confirmEmailVerification(token)
      .then(() => {
        setVerificationState("verified");
        setMessage(null);
      })
      .catch((error) => {
        setVerificationState("error");
        setMessage(error instanceof ApiError ? error.message : "이메일 인증 링크를 확인하지 못했습니다.");
      });
  }, [confirmEmailVerification, token]);

  useEffect(() => {
    if (token || status !== "authenticated" || user?.email_verified) return;

    const refreshVerificationState = () => {
      if (document.visibilityState === "hidden") return;
      void refreshCurrentUser();
    };
    window.addEventListener("focus", refreshVerificationState);
    document.addEventListener("visibilitychange", refreshVerificationState);
    return () => {
      window.removeEventListener("focus", refreshVerificationState);
      document.removeEventListener("visibilitychange", refreshVerificationState);
    };
  }, [refreshCurrentUser, status, token, user?.email_verified]);

  if (status === "guest" && !token) {
    return <Navigate replace to="/login" />;
  }

  async function handleResend() {
    setIsResending(true);
    setMessage(null);
    try {
      await requestEmailVerification();
      setVerificationState("waiting");
      setMessage("인증 메일을 다시 보냈습니다.");
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "인증 메일을 보내지 못했습니다.");
    } finally {
      setIsResending(false);
    }
  }

  const verified = verificationState === "verified" || user?.email_verified === true;

  return (
    <main className="route-page route-page-centered">
      <section className="auth-card verification-card" aria-labelledby="verify-email-title">
        <div className="route-eyebrow">이메일 확인</div>
        <h1 id="verify-email-title">{verified ? "인증이 완료되었습니다" : "이메일을 인증해 주세요"}</h1>
        <p className="route-description">
          {verificationState === "confirming"
            ? "인증 링크를 확인하고 있습니다."
            : verified
              ? "이제 내 기록장의 모든 기능을 사용할 수 있습니다."
              : `${user?.email ?? "가입한 이메일"}로 보낸 인증 링크를 눌러 주세요.`}
        </p>
        {!verified && verificationState !== "confirming" && (
          <p className="verification-hint">메일이 보이지 않으면 스팸함도 확인해 주세요.</p>
        )}
        {message && <p className={verificationState === "error" ? "auth-error" : "auth-success"} role="status">{message}</p>}
        <div className="verification-actions">
          {verified ? (
            <Link className="route-primary-link" to={status === "authenticated" ? "/workspace" : "/login"}>
              {status === "authenticated" ? "내 기록장 열기" : "로그인하기"}
            </Link>
          ) : verificationState !== "confirming" && status === "authenticated" ? (
            <button className="auth-submit" type="button" disabled={isResending} onClick={handleResend}>
              {isResending ? "발송 중..." : "인증 메일 다시 보내기"}
            </button>
          ) : null}
        </div>
      </section>
    </main>
  );
}

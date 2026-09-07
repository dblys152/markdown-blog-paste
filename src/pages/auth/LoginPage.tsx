import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../features/auth/AuthProvider";
import { GoogleIdentityButton } from "../../features/auth/GoogleIdentityButton";
import { ApiError } from "../../shared/api/http";

type GoogleStep =
  | { kind: "signup"; credential: string; email: string }
  | { kind: "link"; credential: string; email: string }
  | null;

export function LoginPage() {
  const { status, login, googleLogin, googleSignup, linkGoogleAndLogin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [googleStep, setGoogleStep] = useState<GoogleStep>(null);

  if (status === "authenticated") {
    return <Navigate replace to="/workspace" />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);
    const form = new FormData(event.currentTarget);

    try {
      await login({
        email: String(form.get("email") ?? "").trim(),
        password: String(form.get("password") ?? ""),
      });
      const destination = (location.state as { from?: string } | null)?.from ?? "/workspace";
      navigate(destination, { replace: true });
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "로그인 중 문제가 발생했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function finishLogin() {
    const destination = (location.state as { from?: string } | null)?.from ?? "/workspace";
    navigate(destination, { replace: true });
  }

  async function handleGoogleCredential(credential: string) {
    setErrorMessage(null);
    setIsSubmitting(true);
    try {
      const result = await googleLogin(credential);
      if ("access_token" in result) {
        finishLogin();
        return;
      }
      setGoogleStep({
        kind: result.status === "signup_required" ? "signup" : "link",
        credential,
        email: result.email,
      });
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Google 로그인을 처리하지 못했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleGoogleCompletion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!googleStep) return;
    setErrorMessage(null);
    setIsSubmitting(true);
    const form = new FormData(event.currentTarget);
    try {
      if (googleStep.kind === "signup") {
        await googleSignup(googleStep.credential, String(form.get("displayName") ?? "").trim());
      } else {
        await linkGoogleAndLogin(googleStep.credential, String(form.get("password") ?? ""));
      }
      finishLogin();
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Google 로그인을 완료하지 못했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="route-page route-page-centered">
      <section className="auth-card" aria-labelledby="login-title">
        <div className="route-eyebrow">내 기록장</div>
        <h1 id="login-title">로그인</h1>
        <p className="route-description">작성한 Markdown 페이지를 어디서든 이어서 관리하세요.</p>
        {googleStep ? (
          <form className="auth-form google-auth-completion" onSubmit={handleGoogleCompletion}>
            <div className="google-auth-account">
              <strong>{googleStep.email}</strong>
              <span>{googleStep.kind === "signup" ? "새 계정으로 가입합니다." : "기존 계정과 Google 계정을 연결합니다."}</span>
            </div>
            {googleStep.kind === "signup" ? (
              <label>
                닉네임
                <input name="displayName" minLength={1} maxLength={10} autoComplete="nickname" placeholder="사용할 닉네임" required autoFocus />
              </label>
            ) : (
              <label>
                기존 계정 비밀번호
                <input name="password" type="password" minLength={8} maxLength={128} autoComplete="current-password" placeholder="비밀번호 확인" required autoFocus />
              </label>
            )}
            {errorMessage && <p className="auth-error" role="alert">{errorMessage}</p>}
            <button className="auth-submit" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "처리 중..." : googleStep.kind === "signup" ? "가입하고 로그인" : "연결하고 로그인"}
            </button>
            <button className="auth-secondary-button" type="button" disabled={isSubmitting} onClick={() => {
              setGoogleStep(null);
              setErrorMessage(null);
            }}>다른 방법으로 로그인</button>
          </form>
        ) : <>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            이메일
            <input type="email" name="email" autoComplete="email" placeholder="name@example.com" required />
          </label>
          <label>
            비밀번호
            <input type="password" name="password" autoComplete="current-password" placeholder="비밀번호" minLength={8} maxLength={128} required />
          </label>
          <Link className="auth-forgot-password" to="/forgot-password">비밀번호를 잊으셨나요?</Link>
          {errorMessage && <p className="auth-error" role="alert">{errorMessage}</p>}
          <button className="auth-submit" type="submit" disabled={isSubmitting || status === "loading"}>
            {isSubmitting ? "로그인 중..." : "로그인"}
          </button>
        </form>
        <div className="auth-divider"><span>또는</span></div>
        <GoogleIdentityButton onCredential={handleGoogleCredential} disabled={isSubmitting} text="signin_with" />
        </>}
        <p className="auth-footer">
          아직 계정이 없나요? <Link to="/signup">회원가입</Link>
        </p>
      </section>
    </main>
  );
}

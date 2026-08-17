import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../features/auth/AuthProvider";
import { ApiError } from "../../shared/api/http";

export function LoginPage() {
  const { status, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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

  return (
    <main className="route-page route-page-centered">
      <section className="auth-card" aria-labelledby="login-title">
        <div className="route-eyebrow">내 기록장</div>
        <h1 id="login-title">로그인</h1>
        <p className="route-description">작성한 Markdown 페이지를 어디서든 이어서 관리하세요.</p>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            이메일
            <input type="email" name="email" autoComplete="email" placeholder="name@example.com" required />
          </label>
          <label>
            비밀번호
            <input type="password" name="password" autoComplete="current-password" placeholder="비밀번호" minLength={8} maxLength={128} required />
          </label>
          {errorMessage && <p className="auth-error" role="alert">{errorMessage}</p>}
          <button className="auth-submit" type="submit" disabled={isSubmitting || status === "loading"}>
            {isSubmitting ? "로그인 중..." : "로그인"}
          </button>
        </form>
        <p className="auth-footer">
          아직 계정이 없나요? <Link to="/signup">회원가입</Link>
        </p>
      </section>
    </main>
  );
}

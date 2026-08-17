import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../../features/auth/AuthProvider";
import { ApiError } from "../../shared/api/http";

export function SignupPage() {
  const { status, signup } = useAuth();
  const navigate = useNavigate();
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
      await signup({
        display_name: String(form.get("displayName") ?? "").trim(),
        email: String(form.get("email") ?? "").trim(),
        password: String(form.get("password") ?? ""),
      });
      navigate("/workspace", { replace: true });
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "회원가입 중 문제가 발생했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="route-page route-page-centered">
      <section className="auth-card" aria-labelledby="signup-title">
        <div className="route-eyebrow">MD2Blog 시작하기</div>
        <h1 id="signup-title">회원가입</h1>
        <p className="route-description">개인 Markdown 기록장을 만들고 나만의 페이지로 관리해보세요.</p>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            이름
            <input type="text" name="displayName" autoComplete="name" placeholder="표시 이름" maxLength={100} required />
          </label>
          <label>
            이메일
            <input type="email" name="email" autoComplete="email" placeholder="name@example.com" required />
          </label>
          <label>
            비밀번호
            <input type="password" name="password" autoComplete="new-password" placeholder="8자 이상 비밀번호" minLength={8} maxLength={128} required />
          </label>
          {errorMessage && <p className="auth-error" role="alert">{errorMessage}</p>}
          <button className="auth-submit" type="submit" disabled={isSubmitting || status === "loading"}>
            {isSubmitting ? "가입 중..." : "회원가입"}
          </button>
        </form>
        <p className="auth-footer">
          이미 계정이 있나요? <Link to="/login">로그인</Link>
        </p>
      </section>
    </main>
  );
}

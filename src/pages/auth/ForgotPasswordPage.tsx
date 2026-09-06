import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { requestPasswordReset } from "../../features/auth/api";
import { ApiError } from "../../shared/api/http";

export function ForgotPasswordPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);
    const form = new FormData(event.currentTarget);
    try {
      await requestPasswordReset(String(form.get("email") ?? "").trim());
      setIsComplete(true);
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "재설정 메일을 보내지 못했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="route-page route-page-centered">
      <section className="auth-card password-recovery-card" aria-labelledby="forgot-password-title">
        <div className="route-eyebrow">계정 복구</div>
        <h1 id="forgot-password-title">비밀번호 찾기</h1>
        {isComplete ? (
          <>
            <p className="route-description">가입된 이메일이라면 비밀번호 재설정 링크를 보냈습니다.</p>
            <p className="verification-hint">메일이 보이지 않으면 스팸함도 확인해 주세요. 링크는 1시간 동안 유효합니다.</p>
            <Link className="route-primary-link auth-centered-link" to="/login">로그인으로 돌아가기</Link>
          </>
        ) : (
          <>
            <p className="route-description">가입할 때 사용한 이메일을 입력해 주세요.</p>
            <form className="auth-form" onSubmit={handleSubmit}>
              <label>
                이메일
                <input type="email" name="email" autoComplete="email" placeholder="name@example.com" required />
              </label>
              {errorMessage && <p className="auth-error" role="alert">{errorMessage}</p>}
              <button className="auth-submit" type="submit" disabled={isSubmitting}>
                {isSubmitting ? "발송 중..." : "재설정 메일 보내기"}
              </button>
            </form>
            <p className="auth-footer"><Link to="/login">로그인으로 돌아가기</Link></p>
          </>
        )}
      </section>
    </main>
  );
}

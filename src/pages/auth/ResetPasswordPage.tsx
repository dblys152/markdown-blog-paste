import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { confirmPasswordReset } from "../../features/auth/api";
import { ApiError } from "../../shared/api/http";

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    const form = new FormData(event.currentTarget);
    const password = String(form.get("password") ?? "");
    const passwordConfirmation = String(form.get("passwordConfirmation") ?? "");
    if (password !== passwordConfirmation) {
      setErrorMessage("비밀번호가 일치하지 않습니다.");
      return;
    }
    if (!token) {
      setErrorMessage("유효하지 않은 비밀번호 재설정 링크입니다.");
      return;
    }

    setIsSubmitting(true);
    try {
      await confirmPasswordReset(token, password);
      setIsComplete(true);
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "비밀번호를 변경하지 못했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="route-page route-page-centered">
      <section className="auth-card password-recovery-card" aria-labelledby="reset-password-title">
        <div className="route-eyebrow">계정 복구</div>
        <h1 id="reset-password-title">{isComplete ? "비밀번호 변경 완료" : "새 비밀번호 설정"}</h1>
        {isComplete ? (
          <>
            <p className="route-description">새 비밀번호가 적용되었습니다. 모든 기기에서 다시 로그인해 주세요.</p>
            <Link className="route-primary-link auth-centered-link" to="/login">새 비밀번호로 로그인</Link>
          </>
        ) : (
          <>
            <p className="route-description">앞으로 사용할 새 비밀번호를 입력해 주세요.</p>
            <form className="auth-form" onSubmit={handleSubmit}>
              <label>
                새 비밀번호
                <input type="password" name="password" autoComplete="new-password" placeholder="8자 이상 비밀번호" minLength={8} maxLength={128} required />
              </label>
              <label>
                새 비밀번호 확인
                <input type="password" name="passwordConfirmation" autoComplete="new-password" placeholder="비밀번호 다시 입력" minLength={8} maxLength={128} required />
              </label>
              {errorMessage && <p className="auth-error" role="alert">{errorMessage}</p>}
              <button className="auth-submit" type="submit" disabled={isSubmitting || !token}>
                {isSubmitting ? "변경 중..." : "비밀번호 변경"}
              </button>
            </form>
          </>
        )}
      </section>
    </main>
  );
}

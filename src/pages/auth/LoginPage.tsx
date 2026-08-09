import { Link } from "react-router-dom";

export function LoginPage() {
  return (
    <main className="route-page route-page-centered">
      <section className="auth-card" aria-labelledby="login-title">
        <div className="route-eyebrow">내 기록장</div>
        <h1 id="login-title">로그인</h1>
        <p className="route-description">작성한 Markdown 페이지를 어디서든 이어서 관리하세요.</p>
        <form className="auth-form" onSubmit={(event) => event.preventDefault()}>
          <label>
            이메일
            <input type="email" name="email" autoComplete="email" placeholder="name@example.com" />
          </label>
          <label>
            비밀번호
            <input type="password" name="password" autoComplete="current-password" placeholder="비밀번호" />
          </label>
          <button className="auth-submit" type="submit" disabled title="FastAPI 인증 연결 후 사용할 수 있습니다.">
            로그인 준비 중
          </button>
        </form>
        <p className="auth-footer">
          아직 계정이 없나요? <Link to="/signup">회원가입</Link>
        </p>
      </section>
    </main>
  );
}

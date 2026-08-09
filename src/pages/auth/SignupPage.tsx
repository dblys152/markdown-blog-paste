import { Link } from "react-router-dom";

export function SignupPage() {
  return (
    <main className="route-page route-page-centered">
      <section className="auth-card" aria-labelledby="signup-title">
        <div className="route-eyebrow">MD2Blog 시작하기</div>
        <h1 id="signup-title">회원가입</h1>
        <p className="route-description">개인 Markdown 기록장을 만들고 나만의 페이지로 관리해보세요.</p>
        <form className="auth-form" onSubmit={(event) => event.preventDefault()}>
          <label>
            이름
            <input type="text" name="name" autoComplete="name" placeholder="표시 이름" />
          </label>
          <label>
            이메일
            <input type="email" name="email" autoComplete="email" placeholder="name@example.com" />
          </label>
          <label>
            비밀번호
            <input type="password" name="password" autoComplete="new-password" placeholder="비밀번호" />
          </label>
          <button className="auth-submit" type="submit" disabled title="FastAPI 인증 연결 후 사용할 수 있습니다.">
            회원가입 준비 중
          </button>
        </form>
        <p className="auth-footer">
          이미 계정이 있나요? <Link to="/login">로그인</Link>
        </p>
      </section>
    </main>
  );
}

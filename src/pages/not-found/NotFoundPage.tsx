import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <main className="route-page route-page-centered">
      <section className="not-found-card">
        <div className="route-eyebrow">404</div>
        <h1>페이지를 찾을 수 없습니다</h1>
        <p className="route-description">주소가 올바른지 확인하거나 빠른 변환 화면으로 돌아가세요.</p>
        <Link className="route-primary-link" to="/">빠른 변환으로 돌아가기</Link>
      </section>
    </main>
  );
}

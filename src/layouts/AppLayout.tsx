import { Link, NavLink, Outlet, useLocation } from "react-router-dom";

export function AppLayout() {
  const location = useLocation();
  const isWorkspace = location.pathname.startsWith("/workspace");

  return (
    <div className={`app-frame ${isWorkspace ? "is-workspace" : ""}`}>
      <header className="app-header">
        <div className="app-brand" aria-label="MD2Blog">
          <strong>MD2Blog</strong>
        </div>

        <nav className="app-top-nav" aria-label="주 메뉴">
          <NavLink className={({ isActive }) => (isActive ? "is-active" : "")} end to="/">
            빠른 변환
          </NavLink>
          <NavLink className={({ isActive }) => (isActive ? "is-active" : "")} to="/workspace">
            내 기록장
          </NavLink>
        </nav>

        <div className="app-header-actions">
          <Link className="app-login-link is-secondary" to="/login">로그인</Link>
          <Link className="app-login-link" to="/signup">회원가입</Link>
        </div>
      </header>

      <div className="app-route-content">
        <Outlet />
      </div>
    </div>
  );
}

import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../features/auth/AuthProvider";

export function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { status, user, logout } = useAuth();
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
          {status === "authenticated" && user ? (
            <>
              <span className="app-user-name">{user.display_name}</span>
              <button
                className="app-logout-button"
                type="button"
                onClick={() => {
                  void logout()
                    .catch(() => undefined)
                    .finally(() => navigate("/"));
                }}
              >
                로그아웃
              </button>
            </>
          ) : status === "guest" ? (
            <Link className="app-login-link" to="/login">로그인</Link>
          ) : (
            <span className="app-auth-loading" aria-label="로그인 상태 확인 중" />
          )}
        </div>
      </header>

      <div className="app-route-content">
        <Outlet />
      </div>
    </div>
  );
}

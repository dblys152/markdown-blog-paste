import { useState, type FormEvent } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../features/auth/AuthProvider";
import { ApiError } from "../shared/api/http";

export function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { status, user, logout, deleteAccount } = useAuth();
  const [isAccountDeletionOpen, setIsAccountDeletionOpen] = useState(false);
  const [isAccountManagementOpen, setIsAccountManagementOpen] = useState(false);
  const [isAccountMenuOpen, setIsAccountMenuOpen] = useState(false);
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);
  const [accountDeletionError, setAccountDeletionError] = useState<string | null>(null);
  const isWorkspace = location.pathname.startsWith("/workspace");

  async function handleDeleteAccount(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAccountDeletionError(null);
    setIsDeletingAccount(true);
    const form = new FormData(event.currentTarget);
    try {
      await deleteAccount(String(form.get("password") ?? ""));
      setIsAccountDeletionOpen(false);
      navigate("/", { replace: true });
    } catch (error) {
      setAccountDeletionError(
        error instanceof ApiError ? error.message : "회원탈퇴를 처리하지 못했습니다.",
      );
    } finally {
      setIsDeletingAccount(false);
    }
  }

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
            <div className="app-account-menu">
              <button
                className="app-account-menu-trigger"
                type="button"
                aria-haspopup="menu"
                aria-expanded={isAccountMenuOpen}
                onClick={() => setIsAccountMenuOpen((open) => !open)}
              >
                <img className="app-account-avatar" src="/madi-avatar.png" alt="" />
                <span className="app-user-name">{user.display_name}</span>
              </button>
              {isAccountMenuOpen && (
                <div className="app-account-menu-popover" role="menu">
                  <button
                    type="button"
                    role="menuitem"
                    onClick={() => {
                      setIsAccountMenuOpen(false);
                      setIsAccountManagementOpen(true);
                    }}
                  >계정 관리</button>
                  <button
                    type="button"
                    role="menuitem"
                    onClick={() => {
                      setIsAccountMenuOpen(false);
                      void logout()
                        .catch(() => undefined)
                        .finally(() => navigate("/"));
                    }}
                  >로그아웃</button>
                </div>
              )}
            </div>
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

      {isAccountManagementOpen && user && (
        <div className="account-deletion-backdrop" role="presentation" onMouseDown={(event) => {
          if (event.target === event.currentTarget) setIsAccountManagementOpen(false);
        }}>
          <section className="account-management-dialog" role="dialog" aria-modal="true" aria-labelledby="account-management-title">
            <div className="account-dialog-heading">
              <div>
                <span>내 계정</span>
                <h2 id="account-management-title">계정 관리</h2>
              </div>
              <button type="button" aria-label="계정 관리 닫기" onClick={() => setIsAccountManagementOpen(false)}>×</button>
            </div>
            <dl className="account-profile-details">
              <div><dt>이름</dt><dd>{user.display_name}</dd></div>
              <div><dt>이메일</dt><dd>{user.email}</dd></div>
              <div><dt>이메일 인증</dt><dd className={user.email_verified ? "is-verified" : ""}>{user.email_verified ? "인증 완료" : "인증 필요"}</dd></div>
            </dl>
            <section className="account-danger-zone" aria-labelledby="account-danger-title">
              <div>
                <strong id="account-danger-title">계정 및 데이터 삭제</strong>
                <p>계정과 저장된 모든 기록을 영구 삭제합니다.</p>
              </div>
              <button type="button" onClick={() => {
                setIsAccountManagementOpen(false);
                setAccountDeletionError(null);
                setIsAccountDeletionOpen(true);
              }}>회원탈퇴</button>
            </section>
          </section>
        </div>
      )}

      {isAccountDeletionOpen && (
        <div className="account-deletion-backdrop" role="presentation" onMouseDown={(event) => {
          if (event.target === event.currentTarget && !isDeletingAccount) {
            setIsAccountDeletionOpen(false);
          }
        }}>
          <section className="account-deletion-dialog" role="dialog" aria-modal="true" aria-labelledby="account-deletion-title">
            <div className="account-dialog-heading">
              <div>
                <span>계정 삭제</span>
                <h2 id="account-deletion-title">회원탈퇴</h2>
              </div>
              <button type="button" aria-label="회원탈퇴 닫기" disabled={isDeletingAccount} onClick={() => setIsAccountDeletionOpen(false)}>×</button>
            </div>
            <p>탈퇴하면 모든 페이지와 휴지통의 내용이 즉시 영구 삭제되며 복구할 수 없습니다.</p>
            <p>모든 로그인 세션도 종료됩니다. 계속하려면 현재 비밀번호를 입력해 주세요.</p>
            <form onSubmit={handleDeleteAccount}>
              <label>
                현재 비밀번호
                <input name="password" type="password" autoComplete="current-password" minLength={8} maxLength={128} required autoFocus />
              </label>
              {accountDeletionError && <p className="auth-error" role="alert">{accountDeletionError}</p>}
              <div className="account-deletion-actions">
                <button type="button" disabled={isDeletingAccount} onClick={() => setIsAccountDeletionOpen(false)}>취소</button>
                <button className="is-danger" type="submit" disabled={isDeletingAccount}>
                  {isDeletingAccount ? "탈퇴 처리 중..." : "영구 탈퇴"}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}

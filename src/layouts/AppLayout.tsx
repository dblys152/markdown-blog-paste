import { useEffect, useState, type FormEvent } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../features/auth/AuthProvider";
import { GoogleIdentityButton } from "../features/auth/GoogleIdentityButton";
import {
  connectGoogle,
  disconnectGoogle,
  getGoogleConnection,
  type GoogleConnection,
} from "../features/auth/api";
import { ApiError } from "../shared/api/http";

export function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { status, user, logout, deleteAccount, deleteGoogleAccount, updateDisplayName } = useAuth();
  const [isAccountDeletionOpen, setIsAccountDeletionOpen] = useState(false);
  const [isAccountManagementOpen, setIsAccountManagementOpen] = useState(false);
  const [isAccountMenuOpen, setIsAccountMenuOpen] = useState(false);
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);
  const [accountDeletionError, setAccountDeletionError] = useState<string | null>(null);
  const [googleDeletionCredential, setGoogleDeletionCredential] = useState<string | null>(null);
  const [isEditingDisplayName, setIsEditingDisplayName] = useState(false);
  const [isSavingDisplayName, setIsSavingDisplayName] = useState(false);
  const [displayNameDraft, setDisplayNameDraft] = useState("");
  const [displayNameError, setDisplayNameError] = useState<string | null>(null);
  const [googleConnection, setGoogleConnection] = useState<GoogleConnection | null>(null);
  const [googleConnectionError, setGoogleConnectionError] = useState<string | null>(null);
  const [isUpdatingGoogleConnection, setIsUpdatingGoogleConnection] = useState(false);
  const isWorkspace = location.pathname.startsWith("/workspace");

  useEffect(() => {
    setGoogleConnection(null);
    setGoogleConnectionError(null);
  }, [user?.id]);

  useEffect(() => {
    if (
      !isAccountManagementOpen
      || status !== "authenticated"
      || googleConnection !== null
    ) return;
    let active = true;
    setGoogleConnectionError(null);
    void getGoogleConnection()
      .then((connection) => { if (active) setGoogleConnection(connection); })
      .catch((error: unknown) => {
        if (active) setGoogleConnectionError(error instanceof ApiError ? error.message : "Google 계정 연결 상태를 확인하지 못했습니다.");
    });
    return () => { active = false; };
  }, [googleConnection, isAccountManagementOpen, status]);

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

  function handleConfirmGoogleIdentity(credential: string) {
    setAccountDeletionError(null);
    setGoogleDeletionCredential(credential);
  }

  async function handleDeleteGoogleAccount() {
    if (!googleDeletionCredential) return;
    setAccountDeletionError(null);
    setIsDeletingAccount(true);
    try {
      await deleteGoogleAccount(googleDeletionCredential);
      setIsAccountDeletionOpen(false);
      setGoogleDeletionCredential(null);
      navigate("/", { replace: true });
    } catch (error) {
      setAccountDeletionError(
        error instanceof ApiError ? error.message : "회원탈퇴를 처리하지 못했습니다.",
      );
    } finally {
      setIsDeletingAccount(false);
    }
  }

  async function handleUpdateDisplayName(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedDisplayName = displayNameDraft.trim();
    if (!normalizedDisplayName) {
      setDisplayNameError("닉네임을 입력해 주세요.");
      return;
    }
    if (normalizedDisplayName === user?.display_name) {
      setIsEditingDisplayName(false);
      setDisplayNameError(null);
      return;
    }
    setDisplayNameError(null);
    setIsSavingDisplayName(true);
    try {
      await updateDisplayName(normalizedDisplayName);
      setIsEditingDisplayName(false);
    } catch (error) {
      setDisplayNameError(
        error instanceof ApiError ? error.message : "닉네임을 변경하지 못했습니다.",
      );
    } finally {
      setIsSavingDisplayName(false);
    }
  }

  async function handleConnectGoogle(credential: string) {
    setGoogleConnectionError(null);
    setIsUpdatingGoogleConnection(true);
    try {
      await connectGoogle(credential);
      setGoogleConnection(await getGoogleConnection());
    } catch (error) {
      setGoogleConnectionError(error instanceof ApiError ? error.message : "Google 계정을 연결하지 못했습니다.");
    } finally {
      setIsUpdatingGoogleConnection(false);
    }
  }

  async function handleDisconnectGoogle() {
    if (!window.confirm("Google 계정 연결을 해제하시겠습니까?")) return;
    setGoogleConnectionError(null);
    setIsUpdatingGoogleConnection(true);
    try {
      await disconnectGoogle();
      setGoogleConnection({ connected: false, email: null, can_disconnect: false });
    } catch (error) {
      setGoogleConnectionError(error instanceof ApiError ? error.message : "Google 계정 연결을 해제하지 못했습니다.");
    } finally {
      setIsUpdatingGoogleConnection(false);
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
                      setIsEditingDisplayName(false);
                      setDisplayNameDraft(user.display_name);
                      setDisplayNameError(null);
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
              <div className="account-display-name-row">
                <dt>닉네임</dt>
                <dd>
                  {isEditingDisplayName ? (
                    <form className="account-display-name-form" onSubmit={handleUpdateDisplayName}>
                      <input
                        aria-label="닉네임"
                        value={displayNameDraft}
                        onChange={(event) => setDisplayNameDraft(event.target.value)}
                        minLength={1}
                        maxLength={10}
                        disabled={isSavingDisplayName}
                        autoFocus
                        required
                      />
                      <button type="submit" disabled={isSavingDisplayName}>저장</button>
                      <button type="button" disabled={isSavingDisplayName} onClick={() => {
                        setIsEditingDisplayName(false);
                        setDisplayNameDraft(user.display_name);
                        setDisplayNameError(null);
                      }}>취소</button>
                    </form>
                  ) : (
                    <span className="account-display-name-value">
                      <span>{user.display_name}</span>
                      <button type="button" aria-label="닉네임 변경" onClick={() => {
                        setDisplayNameDraft(user.display_name);
                        setDisplayNameError(null);
                        setIsEditingDisplayName(true);
                      }}>
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                          <path d="M12 20h9" />
                          <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
                        </svg>
                      </button>
                    </span>
                  )}
                  {displayNameError && <span className="account-display-name-error" role="alert">{displayNameError}</span>}
                </dd>
              </div>
              <div><dt>이메일</dt><dd>{user.email}</dd></div>
              <div><dt>이메일 인증</dt><dd className={user.email_verified ? "is-verified" : ""}>{user.email_verified ? "인증 완료" : "인증 필요"}</dd></div>
            </dl>
            <section className="account-google-section" aria-labelledby="account-google-title">
              <div className="account-google-heading">
                <div>
                  <strong id="account-google-title">Google 계정</strong>
                  <p>Google 계정으로 간편하게 로그인할 수 있습니다.</p>
                </div>
                {googleConnection?.connected && <span className="account-connected-badge">연결됨</span>}
              </div>
              {googleConnection === null && !googleConnectionError ? (
                <span className="account-google-loading">연결 상태 확인 중...</span>
              ) : googleConnection?.connected ? (
                <div className="account-google-connection">
                  <span>{googleConnection.email}</span>
                  {googleConnection.can_disconnect && (
                    <button type="button" disabled={isUpdatingGoogleConnection} onClick={() => void handleDisconnectGoogle()}>
                      연결 해제
                    </button>
                  )}
                </div>
              ) : (
                <GoogleIdentityButton onCredential={handleConnectGoogle} disabled={isUpdatingGoogleConnection} />
              )}
              {googleConnectionError && <p className="account-display-name-error" role="alert">{googleConnectionError}</p>}
            </section>
            <section className="account-danger-zone" aria-labelledby="account-danger-title">
              <div>
                <strong id="account-danger-title">계정 및 데이터 삭제</strong>
                <p>계정과 저장된 모든 기록을 영구 삭제합니다.</p>
              </div>
              <button type="button" onClick={() => {
                setIsAccountManagementOpen(false);
                setAccountDeletionError(null);
                setGoogleDeletionCredential(null);
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
            setGoogleDeletionCredential(null);
          }
        }}>
          <section className="account-deletion-dialog" role="dialog" aria-modal="true" aria-labelledby="account-deletion-title">
            <div className="account-dialog-heading">
              <div>
                <span>계정 삭제</span>
                <h2 id="account-deletion-title">회원탈퇴</h2>
              </div>
              <button type="button" aria-label="회원탈퇴 닫기" disabled={isDeletingAccount} onClick={() => {
                setIsAccountDeletionOpen(false);
                setGoogleDeletionCredential(null);
              }}>×</button>
            </div>
            <p>탈퇴하면 모든 데이터가 영구 삭제되고 모든 기기에서 로그아웃됩니다.</p>
            <p>계속하려면 본인 확인을 진행해 주세요.</p>
            {googleConnection?.connected && !googleConnection.can_disconnect ? (
              <div className="account-google-deletion">
                {googleDeletionCredential ? (
                  <div className="account-google-verification" role="status">
                    <span aria-hidden="true">✓</span>
                    <div>
                      <strong>본인 확인 완료</strong>
                      <p>{googleConnection.email}</p>
                    </div>
                  </div>
                ) : (
                  <div className="account-google-verification-request">
                    <strong>Google 계정으로 본인 확인</strong>
                    <p>연결된 Google 계정을 확인한 뒤 탈퇴를 진행할 수 있습니다.</p>
                    <GoogleIdentityButton onCredential={handleConfirmGoogleIdentity} disabled={isDeletingAccount} text="continue_with" />
                  </div>
                )}
                {accountDeletionError && <p className="auth-error" role="alert">{accountDeletionError}</p>}
                <div className="account-deletion-actions">
                  <button type="button" disabled={isDeletingAccount} onClick={() => {
                    setIsAccountDeletionOpen(false);
                    setGoogleDeletionCredential(null);
                  }}>취소</button>
                  <button
                    className="is-danger"
                    type="button"
                    disabled={isDeletingAccount || !googleDeletionCredential}
                    onClick={() => void handleDeleteGoogleAccount()}
                  >{isDeletingAccount ? "탈퇴 처리 중..." : "영구 탈퇴"}</button>
                </div>
              </div>
            ) : <form onSubmit={handleDeleteAccount}>
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
            </form>}
          </section>
        </div>
      )}
    </div>
  );
}

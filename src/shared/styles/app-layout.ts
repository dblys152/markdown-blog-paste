export const APP_LAYOUT_CSS = `
.app-frame {
  display: grid;
  grid-template-rows: 68px minmax(0, 1fr);
  height: 100dvh;
  min-height: 0;
  overflow: hidden;
  background: #f7f8fa;
  color: #172033;
}

.app-header {
  position: relative;
  z-index: 40;
  display: flex;
  min-width: 0;
  align-items: stretch;
  gap: 26px;
  padding: 0 28px;
  border-bottom: 1px solid #dfe3eb;
  background: #fff;
}

.app-brand {
  display: inline-flex;
  align-items: center;
  color: #17213b;
  text-decoration: none;
}

.app-brand strong { font-size: 23px; letter-spacing: -0.04em; }

.app-top-nav {
  display: flex;
  align-items: stretch;
  gap: 18px;
}

.app-top-nav a {
  position: relative;
  display: inline-flex;
  align-items: center;
  padding: 0 8px;
  color: #303849;
  font-size: 15px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -.02em;
  text-decoration: none;
}

.app-top-nav a::after {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  height: 3px;
  border-radius: 3px 3px 0 0;
  background: #3f5bea;
  content: "";
  opacity: 0;
}

.app-top-nav a.is-active { color: #2949df; }
.app-top-nav a.is-active::after { opacity: 1; }

.app-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.app-login-link {
  display: inline-flex;
  height: 38px;
  align-items: center;
  justify-content: center;
  border: 1px solid #3f5bea;
  border-radius: 7px;
  background: #3f5bea;
  color: #fff;
  text-decoration: none;
}

.app-login-link { padding: 0 16px; font-size: 13px; font-weight: 800; transition: background-color .15s, border-color .15s, color .15s, box-shadow .15s; }
.app-login-link:hover { border-color: #2949df; background: #2949df; }
.app-login-link:focus-visible { outline: 0; box-shadow: 0 0 0 3px rgba(63, 91, 234, .2); }
.app-user-name { max-width: 140px; overflow: hidden; color: #374151; font-size: 13px; font-weight: 800; text-overflow: ellipsis; white-space: nowrap; }
.app-logout-button { height: 36px; padding: 0 12px; border: 1px solid #d6dbe5; border-radius: 7px; background: #fff; color: #4b5563; font: inherit; font-size: 12px; font-weight: 800; cursor: pointer; }
.app-logout-button:hover { border-color: #aeb7c6; background: #f8fafc; }
.app-auth-loading { width: 18px; height: 18px; border: 2px solid #dbe1ea; border-top-color: #3f5bea; border-radius: 50%; animation: app-auth-spin .7s linear infinite; }
@keyframes app-auth-spin { to { transform: rotate(360deg); } }

.app-route-content { min-width: 0; min-height: 0; overflow: hidden; }

.route-page {
  min-height: 100%;
  padding: 32px;
  overflow: auto;
  background: #f6f7f9;
}

.route-page-centered { display: grid; place-items: center; }

.auth-card,
.workspace-gate,
.not-found-card {
  width: min(100%, 460px);
  padding: 36px;
  border: 1px solid #dfe4ea;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 20px 48px rgba(15, 23, 42, 0.08);
}

.route-eyebrow { margin-bottom: 10px; color: #3f5bea; font-size: 12px; font-weight: 800; letter-spacing: .08em; }
.route-page h1 { margin: 0; color: #111827; font-size: 28px; letter-spacing: -.03em; }
.route-description { margin: 14px 0 0; color: #667085; line-height: 1.7; }
.auth-form { display: grid; gap: 16px; margin-top: 28px; }
.auth-form label { display: grid; gap: 8px; color: #374151; font-size: 13px; font-weight: 700; }
.auth-form input { width: 100%; height: 44px; padding: 0 12px; border: 1px solid #d1d5db; border-radius: 8px; background: #fff; }
.auth-form input:focus { border-color: #3f5bea; outline: 3px solid rgba(63,91,234,.12); }
.auth-submit { min-height: 44px; border: 0; border-radius: 8px; background: #3f5bea; color: #fff; font-weight: 800; }
.auth-submit:not(:disabled) { cursor: pointer; }
.auth-submit:disabled { opacity: .62; }
.auth-error { margin: -2px 0 0; padding: 10px 12px; border-radius: 7px; background: #fff1f2; color: #be123c; font-size: 12px; font-weight: 700; line-height: 1.5; }
.auth-footer { margin: 22px 0 0; color: #6b7280; font-size: 13px; text-align: center; }
.auth-footer a { color: #2949df; font-weight: 800; }
.not-found-card { text-align: center; }
.route-primary-link { display: inline-flex; min-height: 42px; margin-top: 24px; padding: 0 18px; align-items: center; border-radius: 8px; background: #3f5bea; color: #fff; font-weight: 800; text-decoration: none; }

.workspace-shell {
  display: grid;
  --workspace-sidebar-width: 280px;
  --workspace-editor-size: .48fr;
  grid-template-columns: var(--workspace-sidebar-width) minmax(360px, var(--workspace-editor-size)) 14px minmax(460px, 1fr);
  height: 100%;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background: #fff;
}

.workspace-mobile-tabs { display: none; }

.workspace-loading-state { display: grid; min-height: 0; place-content: center; justify-items: center; gap: 14px; background: #fff; color: #475467; font-size: 13px; }
.workspace-loading-spinner { width: 24px; height: 24px; border: 2px solid #dfe4ee; border-top-color: #3f5bea; border-radius: 50%; animation: workspace-loading-spin .7s linear infinite; }
.workspace-loading-state button { min-height: 36px; padding: 0 14px; border: 1px solid #d8dde6; border-radius: 7px; background: #fff; color: #344054; font-weight: 750; cursor: pointer; }
@keyframes workspace-loading-spin { to { transform: rotate(360deg); } }

.workspace-sidebar {
  display: flex;
  min-height: 0;
  flex-direction: column;
  border-right: 1px solid #dfe3eb;
  background: #fbfcfe;
}

.workspace-sidebar button { font: inherit; }
.workspace-sidebar-title { display: flex; height: 54px; align-items: center; padding: 0 22px; border-bottom: 1px solid #e4e7ed; }
.workspace-sidebar-title strong { color: #1f2937; font-size: 14px; font-weight: 800; }

.workspace-pages-heading { display: flex; align-items: center; justify-content: space-between; padding: 17px 15px 8px 22px; color: #667085; font-size: 11px; font-weight: 800; }
.workspace-pages-heading a, .workspace-pages-heading button { position: relative; display: grid; width: 28px; height: 28px; place-items: center; border: 0; border-radius: 6px; background: transparent; color: #344054; font-size: 21px; line-height: 1; text-decoration: none; cursor: pointer; }
.workspace-pages-heading a:hover, .workspace-pages-heading button:hover { background: #e9edff; color: #2949df; }
.workspace-root-page-add::after { position: absolute; z-index: 30; top: calc(100% + 6px); right: 0; width: max-content; padding: 6px 8px; border-radius: 5px; background: #202938; color: #fff; content: attr(data-tooltip); font-size: 11px; font-weight: 600; line-height: 1.35; opacity: 0; pointer-events: none; white-space: nowrap; box-shadow: 0 6px 18px rgba(15, 23, 42, .2); transform: translateY(-2px); transition: opacity .1s ease .12s, transform .1s ease .12s; }
.workspace-root-page-add:hover::after, .workspace-root-page-add:focus-visible::after { opacity: 1; transform: translateY(0); }

.workspace-page-item { display: grid; grid-template-columns: 22px minmax(0,1fr); gap: 8px; align-items: center; height: 38px; margin: 0 10px; padding: 0 10px 0 14px; border: 0; border-radius: 6px; background: transparent; color: #344054; font-size: 13px; cursor: pointer; text-align: left; }
.workspace-page-item:hover { background: #f2f4f8; }
.workspace-page-item.is-active { background: #edf0ff; color: #2949df; font-weight: 750; }
.workspace-page-item.is-active:hover { background: #e7ebff; }
.workspace-page-node > .workspace-page-item { grid-template-columns: minmax(0,1fr) auto; gap: 4px; cursor: default; }
.workspace-page-node > .workspace-page-item.is-dragging { opacity: .45; }
.workspace-page-node > .workspace-page-item.drop-before { box-shadow: inset 0 2px #4263eb; }
.workspace-page-node > .workspace-page-item.drop-after { box-shadow: inset 0 -2px #4263eb; }
.workspace-page-node > .workspace-page-item.drop-inside { outline: 2px solid #8095ff; outline-offset: -2px; background: #edf0ff; }
.workspace-page-select { position: relative; display: flex; min-width: 0; align-items: center; gap: 8px; overflow: visible; border: 0; background: transparent; color: inherit; font: inherit; text-align: left; cursor: pointer; }
.workspace-page-select:hover, .workspace-page-select:active { border-color: transparent; box-shadow: none; transform: none; }
.workspace-page-select span:last-child { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.workspace-page-actions { position: relative; display: flex; opacity: 0; }
.workspace-page-item:hover .workspace-page-actions, .workspace-page-item:focus-within .workspace-page-actions { opacity: 1; }
.workspace-page-actions button { display: grid; width: 22px; height: 24px; place-items: center; border: 0; border-radius: 4px; background: transparent; color: #667085; font-size: 14px; line-height: 1; cursor: pointer; }
.workspace-page-actions button:hover { background: #dfe5ff; color: #2949df; }
.workspace-page-add-button::after { position: absolute; z-index: 30; top: calc(100% + 6px); right: 0; width: max-content; padding: 6px 8px; border-radius: 5px; background: #202938; color: #fff; content: attr(data-tooltip); font-size: 11px; font-weight: 600; line-height: 1.35; opacity: 0; pointer-events: none; white-space: nowrap; box-shadow: 0 6px 18px rgba(15, 23, 42, .2); transform: translateY(-2px); transition: opacity .1s ease .12s, transform .1s ease .12s; }
.workspace-page-add-button:hover::after, .workspace-page-add-button:focus-visible::after { opacity: 1; transform: translateY(0); }
.workspace-page-rename-input { min-width: 0; height: 28px; padding: 0 7px; border: 1px solid #8095ff; border-radius: 5px; outline: none; background: #fff; color: #253b80; font: inherit; }
.workspace-page-actions .workspace-page-menu { position: absolute; z-index: 20; top: 28px; right: 0; display: grid; width: 112px; padding: 5px; border: 1px solid #dfe3eb; border-radius: 7px; background: #fff; box-shadow: 0 10px 28px rgba(15, 23, 42, .16); }
.workspace-page-actions .workspace-page-menu button { display: block; width: 100%; height: 30px; padding: 0 9px; color: #344054; font-size: 12px; line-height: 30px; text-align: left; white-space: nowrap; }
.workspace-page-actions .workspace-page-menu button.is-danger { color: #dc2626; }
.workspace-empty-pages { margin: 12px 22px; color: #98a2b3; font-size: 12px; line-height: 1.7; }

.workspace-guest-card { position: relative; margin: 18px 12px 0; padding: 15px; border: 1px solid #d9def8; border-radius: 9px; background: #f7f8ff; }
.workspace-guest-card > button { position: absolute; top: 7px; right: 8px; border: 0; background: transparent; color: #7a8496; cursor: pointer; }
.workspace-guest-card strong { color: #273453; font-size: 12px; }
.workspace-guest-card p { margin: 8px 0 12px; color: #697386; font-size: 11px; line-height: 1.55; }
.workspace-guest-card a { color: #2949df; font-size: 11px; font-weight: 800; text-decoration: none; }
.workspace-sidebar-footer { display: flex; gap: 8px; margin: auto 12px 14px; padding: 12px; border: 1px solid #e1e5ec; border-radius: 8px; color: #747e8e; font-size: 10px; line-height: 1.45; }

.workspace-editor,
.workspace-preview { display: grid; min-width: 0; min-height: 0; grid-template-rows: 52px minmax(0,1fr) 36px; background: #fff; }
.workspace-editor { border-right: 1px solid #e0e4eb; }
.workspace-editor-heading { display: flex; min-width: 0; align-items: center; justify-content: space-between; gap: 12px; padding: 0 18px; overflow: hidden; border-bottom: 1px solid #dfe3eb; color: #303849; }
.workspace-editor-heading > div:first-child { display: flex; flex: 0 0 auto; align-items: center; gap: 10px; }
.workspace-editor-heading > div:first-child span { font-size: 17px; }
.workspace-editor-heading strong { font-size: 14px; font-weight: 700; }
.workspace-document-state { display: flex; min-width: 0; flex: 1 1 auto; align-items: center; justify-content: flex-end; gap: 5px; overflow: hidden; color: #667085; font-size: 11px; white-space: nowrap; }
.workspace-document-title { min-width: 0; overflow: hidden; color: #475467; font-weight: 700; text-overflow: ellipsis; }
.workspace-document-title-input { width: 100%; min-width: 40px; max-width: 220px; flex: 1 1 auto; overflow: hidden; border: 1px solid transparent; border-radius: 5px; background: transparent; color: #475467; font: inherit; font-weight: 700; text-align: right; text-overflow: ellipsis; }
.workspace-document-title-input:hover, .workspace-document-title-input:focus { border-color: #cbd3ea; outline: none; background: #fff; }
.workspace-document-state > span[aria-hidden="true"], .workspace-save-label { flex: 0 0 auto; }
.workspace-save-label.save-saving { color: #b86f00; }
.workspace-save-label.save-saved { color: #16a34a; }
.workspace-save-label.save-error { color: #dc2626; }

.workspace-code-area { display: grid; min-width: 0; min-height: 0; grid-template-columns: 44px minmax(0,1fr); overflow: hidden; }
.workspace-line-numbers { display: flex; padding: 12px 8px; flex-direction: column; overflow: hidden; border-right: 1px solid #edf0f4; background: #fafbfc; color: #98a1b0; font: 12px/1.7 ui-monospace, SFMono-Regular, Menlo, monospace; text-align: right; }
.workspace-code-area textarea { width: 100%; height: 100%; min-width: 0; resize: none; padding: 12px 14px 60px; border: 0; outline: 0; background: #fff; color: #20293a; font: 13px/1.7 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; tab-size: 2; white-space: pre; }

.workspace-statusbar { display: flex; min-width: 0; align-items: center; gap: clamp(10px, 2vw, 24px); padding: 0 14px; overflow: hidden; border-top: 1px solid #e4e7ed; color: #667085; font-size: 11px; white-space: nowrap; }
.workspace-statusbar span { flex: 0 0 auto; }
.workspace-statusbar span:last-child { margin-left: auto; }
.workspace-statusbar .save-saving { color: #c27a00; }
.workspace-statusbar .save-saved { color: #16a34a; }
.workspace-statusbar .save-error { color: #dc2626; }

.workspace-divider { position: relative; z-index: 10; display: grid; width: 14px; place-items: center; cursor: col-resize; touch-action: none; isolation: isolate; }
.workspace-divider::before { position: absolute; z-index: -1; inset-block: 0; left: 50%; width: 1px; background: #dfe3eb; content: ""; transform: translateX(-50%); }
.workspace-divider span { position: relative; z-index: 1; display: grid; width: 24px; height: 42px; place-items: center; border: 1px solid #d9dee7; border-radius: 9px; background: #fff; color: #7a8494; box-shadow: 0 2px 8px rgba(15,23,42,.08); transition: border-color .15s, color .15s, box-shadow .15s; }
.workspace-divider:hover span,
.workspace-divider:focus-visible span,
.workspace-shell.is-resizing .workspace-divider span { border-color: #3f5bea; color: #2949df; box-shadow: 0 2px 12px rgba(63,91,234,.2); }
.workspace-divider:focus { outline: none; }
.workspace-shell.is-resizing { cursor: col-resize; user-select: none; }

.workspace-preview-heading { display: flex; align-items: center; justify-content: space-between; padding: 0 22px; border-bottom: 1px solid #dfe3eb; }
.workspace-preview-heading strong { font-size: 13px; }
.workspace-preview iframe { width: 100%; height: 100%; border: 0; background: #fff; }
.workspace-statusbar.is-preview { justify-content: flex-end; }
.workspace-statusbar.is-preview span:last-child { margin-left: 0; }

.document-actions { display: flex; align-items: center; gap: 7px; }
.document-actions > button,
.document-export > button {
  display: inline-flex;
  min-height: 34px;
  padding: 0 11px;
  align-items: center;
  gap: 6px;
  border: 1px solid #d8dde6;
  border-radius: 6px;
  background: #fff;
  color: #344054;
  font-size: 12px;
  font-weight: 750;
  cursor: pointer;
}
.document-actions button:disabled { cursor: not-allowed; opacity: .5; }
.document-actions .document-save-button { border-color: #3f5bea; background: #3f5bea; color: #fff; }
.document-actions .document-save-button svg { width: 15px; height: 15px; }
.document-export { position: relative; }
.document-export-menu {
  position: absolute;
  top: calc(100% + 7px);
  right: 0;
  z-index: 60;
  display: grid;
  width: 238px;
  padding: 6px;
  border: 1px solid #dfe3eb;
  border-radius: 9px;
  background: #fff;
  box-shadow: 0 16px 36px rgba(15,23,42,.14);
}
.document-export-menu button { display: grid; grid-template-columns: 28px minmax(0,1fr); gap: 8px; padding: 10px; border: 0; border-radius: 6px; background: transparent; color: #344054; text-align: left; cursor: pointer; }
.document-export-menu button:hover { background: #f2f4f8; }
.document-export-menu button > span:first-child { padding-top: 2px; font-family: ui-monospace, monospace; }
.document-export-menu button > span:last-child { display: grid; gap: 3px; }
.document-export-menu strong { font-size: 12px; }
.document-export-menu small { color: #7a8495; font-size: 10px; font-weight: 500; }

.save-dialog-backdrop {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(15, 23, 42, .42);
}
.save-dialog {
  width: min(100%, 440px);
  padding: 24px;
  border: 1px solid #e0e4eb;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 24px 64px rgba(15, 23, 42, .22);
}
.save-dialog h2 { margin: 0; color: #172033; font-size: 20px; letter-spacing: -.02em; }
.save-dialog > p { margin: 9px 0 20px; color: #667085; font-size: 13px; }
.save-dialog fieldset { display: grid; gap: 10px; margin: 0; padding: 0; border: 0; }
.save-dialog label { display: flex; min-height: 46px; gap: 10px; align-items: center; padding: 0 13px; border: 1px solid #dfe3eb; border-radius: 8px; color: #344054; font-size: 13px; font-weight: 700; cursor: pointer; }
.save-dialog label:has(input:checked) { border-color: #3f5bea; background: #f5f7ff; color: #2949df; }
.save-dialog input { margin: 0; accent-color: #3f5bea; }
.save-dialog fieldset small { margin: -3px 4px 2px 28px; color: #c2410c; font-size: 11px; }
.save-dialog .save-dialog-select-label { display: block; min-height: 0; margin-bottom: 7px; padding: 0; border: 0; color: #475467; font-size: 12px; cursor: default; }
.save-dialog .save-dialog-select-label:hover { background: transparent; }
.save-dialog-select { width: 100%; height: 42px; margin-bottom: 16px; padding: 0 11px; border: 1px solid #d8dde6; border-radius: 7px; background: #fff; color: #344054; font: inherit; }
.save-dialog-select:focus { border-color: #637df2; outline: 2px solid #e5e9ff; }
.save-dialog-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 22px; }
.save-dialog-actions button { min-height: 38px; padding: 0 15px; border: 1px solid #d8dde6; border-radius: 7px; background: #fff; color: #344054; font-weight: 750; cursor: pointer; }
.save-dialog-actions button.is-primary { border-color: #3f5bea; background: #3f5bea; color: #fff; }
.save-dialog-actions button:disabled { cursor: not-allowed; opacity: .55; }

@media (max-width: 1180px) {
  .workspace-shell { --workspace-sidebar-width: 200px; grid-template-columns: var(--workspace-sidebar-width) minmax(300px, var(--workspace-editor-size)) 14px minmax(390px, 1fr); }
}

@media (max-width: 920px) {
  .app-header { gap: 14px; padding: 0 16px; }
  .app-brand strong { font-size: 20px; }
  .workspace-shell {
    display: grid;
    grid-template-columns: 1fr;
    grid-template-rows: 48px minmax(0, 1fr);
    overflow: hidden;
  }
  .workspace-mobile-tabs {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 3px;
    padding: 5px 10px;
    border-bottom: 1px solid #dfe3eb;
    background: #f7f8fa;
  }
  .workspace-mobile-tabs button {
    border: 0;
    border-radius: 6px;
    background: transparent;
    color: #667085;
    font-size: 12px;
    font-weight: 800;
  }
  .workspace-mobile-tabs button[aria-selected="true"] {
    background: #fff;
    color: #2949df;
    box-shadow: 0 1px 4px rgba(15,23,42,.1);
  }
  .workspace-sidebar,
  .workspace-editor,
  .workspace-preview,
  .workspace-divider { display: none; }
  .workspace-shell.mobile-pane-pages .workspace-sidebar,
  .workspace-shell.mobile-pane-editor .workspace-editor,
  .workspace-shell.mobile-pane-preview .workspace-preview { display: grid; }
  .workspace-shell.mobile-pane-pages .workspace-sidebar { display: flex; }
  .workspace-sidebar { min-height: 0; border-right: 0; border-bottom: 0; overflow: auto; }
  .workspace-sidebar-footer { display: none; }
  .workspace-guest-card { margin-bottom: 14px; }
  .workspace-editor,
  .workspace-preview { height: auto; min-height: 0; }
  .workspace-editor-heading,
  .workspace-preview-heading { padding-inline: 12px; }
  .workspace-document-state { gap: 4px; }
  .workspace-document-title { max-width: 96px; overflow: hidden; text-overflow: ellipsis; }
  .workspace-preview-heading .document-actions { gap: 4px; }
  .workspace-preview-heading .document-actions > button,
  .workspace-preview-heading .document-export > button { width: 34px; min-height: 34px; padding: 0; justify-content: center; }
  .workspace-preview-heading .document-actions > button > span:last-child,
  .workspace-preview-heading .document-export > button > span:last-child { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); }
}

@media (max-width: 680px) {
  .app-frame { grid-template-rows: 60px minmax(0,1fr); }
  .app-header { gap: 8px; padding: 0 12px; }
  .app-brand strong { font-size: 18px; }
  .app-top-nav { gap: 2px; }
  .app-top-nav a { padding-inline: 7px; font-size: 12px; }
  .app-login-link { height: 34px; padding: 0 10px; font-size: 11px; }
  .app-user-name { max-width: 74px; font-size: 11px; }
  .app-logout-button { height: 34px; padding: 0 8px; font-size: 11px; }
  .route-page { padding: 20px; }
  .auth-card, .not-found-card { padding: 26px 22px; }
}
`;

import { Route, Routes } from "react-router-dom";
import { AppLayout } from "../layouts/AppLayout";
import { LoginPage } from "../pages/auth/LoginPage";
import { ForgotPasswordPage } from "../pages/auth/ForgotPasswordPage";
import { ResetPasswordPage } from "../pages/auth/ResetPasswordPage";
import { SignupPage } from "../pages/auth/SignupPage";
import { VerifyEmailPage } from "../pages/auth/VerifyEmailPage";
import { MarkdownPastePage } from "../pages/markdown-paste/MarkdownPastePage";
import { NotFoundPage } from "../pages/not-found/NotFoundPage";
import { WorkspaceGatePage } from "../pages/workspace/WorkspaceGatePage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<MarkdownPastePage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="forgot-password" element={<ForgotPasswordPage />} />
        <Route path="reset-password" element={<ResetPasswordPage />} />
        <Route path="signup" element={<SignupPage />} />
        <Route path="verify-email" element={<VerifyEmailPage />} />
        <Route path="workspace" element={<WorkspaceGatePage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

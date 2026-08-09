import { Route, Routes } from "react-router-dom";
import { AppLayout } from "../layouts/AppLayout";
import { LoginPage } from "../pages/auth/LoginPage";
import { SignupPage } from "../pages/auth/SignupPage";
import { MarkdownPastePage } from "../pages/markdown-paste/MarkdownPastePage";
import { NotFoundPage } from "../pages/not-found/NotFoundPage";
import { WorkspaceGatePage } from "../pages/workspace/WorkspaceGatePage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<MarkdownPastePage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="signup" element={<SignupPage />} />
        <Route path="workspace" element={<WorkspaceGatePage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

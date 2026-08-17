import { BrowserRouter } from "react-router-dom";
import { AppRoutes } from "./app/router";
import { AuthProvider } from "./features/auth/AuthProvider";
import { APP_LAYOUT_CSS } from "./shared/styles/app-layout";
import { APP_CSS } from "./shared/styles/styles";

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <style>{APP_CSS}</style>
        <style>{APP_LAYOUT_CSS}</style>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

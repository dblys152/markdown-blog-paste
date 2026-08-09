import { BrowserRouter } from "react-router-dom";
import { AppRoutes } from "./app/router";
import { APP_LAYOUT_CSS } from "./shared/styles/app-layout";
import { APP_CSS } from "./shared/styles/styles";

export function App() {
  return (
    <BrowserRouter>
      <style>{APP_CSS}</style>
      <style>{APP_LAYOUT_CSS}</style>
      <AppRoutes />
    </BrowserRouter>
  );
}

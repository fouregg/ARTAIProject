import { Route, Routes } from "react-router-dom";

import DomePage from "./pages/DomePage";
import GalleryPage from "./pages/GalleryPage";
import PromptPage from "./pages/PromptPage";

/**
 * Вход и регистрация живут в модалке на самой странице ввода, отдельных экранов нет:
 * гость сначала видит, что за сервис, и вводит код только когда отправляет запрос.
 */
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<PromptPage />} />
      <Route path="/gallery" element={<GalleryPage />} />
      <Route path="/dome" element={<DomePage />} />
      <Route path="*" element={<PromptPage />} />
    </Routes>
  );
}

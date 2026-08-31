/**
 * Фирменные знаки.
 *
 * Наверху — знак самого события, внизу оператор сервиса (АНО «Таврида.Арт») и
 * грантодатель (ПФКИ): его показ предусмотрен условиями гранта, см. согласие на
 * обработку персональных данных.
 *
 * На русском интерфейсе знаки русские, на любом другом — английские версии.
 */
import { useI18n } from "../i18n/LanguageContext";

function useEnglishMarks(): boolean {
  const { uiLanguage } = useI18n();
  return uiLanguage !== "ru";
}

export function EventLogo() {
  const english = useEnglishMarks();

  return (
    <img
      className="brand__event"
      src={english ? "/brand/mfm-en.svg" : "/brand/mfm.svg"}
      alt={english ? "International Festival of Youth 2026" : "Международный фестиваль молодёжи 2026"}
    />
  );
}

export function BrandFooter() {
  const english = useEnglishMarks();

  return (
    <footer className="brandbar">
      <img
        className="brandbar__mark"
        src={english ? "/brand/tavrida-en.svg" : "/brand/tavrida.webp"}
        alt={english ? "Tavrida.Art" : "Таврида.Арт"}
      />
      <img
        className="brandbar__mark brandbar__mark--wide"
        src={english ? "/brand/pfki-en.svg" : "/brand/pfki.svg"}
        alt={
          english
            ? "Presidential Foundation for Cultural Initiatives"
            : "Президентский фонд культурных инициатив"
        }
      />
    </footer>
  );
}

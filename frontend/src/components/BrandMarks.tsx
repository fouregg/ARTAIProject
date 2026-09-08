/**
 * Фирменные знаки.
 *
 * Наверху слева — грантодатель (ПФКИ): его показ предусмотрен условиями гранта,
 * см. согласие на обработку персональных данных. Внизу по центру — событие
 * (Международный фестиваль молодёжи), фестиваль молодого искусства «Таврида.АРТ»
 * как оператор сервиса и знак самого проекта — выставки молодых художников.
 *
 * На русском интерфейсе знаки русские, на любом другом — английские версии.
 * Знак выставки двуязычный сам по себе и не переключается.
 */
import { useI18n } from "../i18n/LanguageContext";

function useEnglishMarks(): boolean {
  const { uiLanguage } = useI18n();
  return uiLanguage !== "ru";
}

export function GrantMark() {
  const english = useEnglishMarks();

  return (
    <img
      className="brand__grant"
      src={english ? "/brand/pfki-en.svg" : "/brand/pfki.svg"}
      alt={
        english
          ? "Presidential Foundation for Cultural Initiatives"
          : "Президентский фонд культурных инициатив"
      }
    />
  );
}

export function BrandFooter() {
  const english = useEnglishMarks();

  return (
    <footer className="brandbar">
      <img
        className="brandbar__mark brandbar__mark--mfm"
        src={english ? "/brand/mfm-en.svg" : "/brand/mfm.svg"}
        alt={english ? "International Festival of Youth 2026" : "Международный фестиваль молодёжи 2026"}
      />
      <img
        className="brandbar__mark"
        src={english ? "/brand/tavrida-en.svg" : "/brand/tavrida.webp"}
        alt={english ? "Tavrida.Art" : "Таврида.Арт"}
      />
      <img
        className="brandbar__mark brandbar__mark--tall"
        src="/brand/exhibition.webp"
        alt={english ? "International Exhibition of Young Artists" : "Международная выставка молодых художников"}
      />
    </footer>
  );
}

import { useEffect, useRef, useState } from "react";

import { useI18n } from "../i18n/LanguageContext";
import { LANGUAGE_NAMES, UI_LANGUAGES } from "../i18n/messages";
import type { UiLanguage } from "../i18n/messages";

/**
 * Выбор языка интерфейса.
 *
 * Нативный select не умеет показывать флаги, поэтому список свой: кнопка с текущим
 * флагом и всплывающее меню. Флаг арабского — Лиги арабских государств: язык не
 * принадлежит одной стране.
 */
export default function LanguageSelect() {
  const { uiLanguage, setChoice } = useI18n();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  function choose(language: UiLanguage) {
    setChoice(language);
    setOpen(false);
  }

  return (
    <div className="langselect" ref={rootRef}>
      <button
        type="button"
        className="langselect__button"
        onClick={() => setOpen((value) => !value)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={LANGUAGE_NAMES[uiLanguage]}
      >
        <img className="langselect__flag" src={`/flags/${uiLanguage}.svg`} alt="" />
        <span>{LANGUAGE_NAMES[uiLanguage]}</span>
        <span className="langselect__caret" aria-hidden="true">
          ▾
        </span>
      </button>

      {open && (
        <ul className="langselect__list" role="listbox">
          {UI_LANGUAGES.map((language) => (
            <li key={language}>
              <button
                type="button"
                role="option"
                aria-selected={language === uiLanguage}
                className={`langselect__option${
                  language === uiLanguage ? " langselect__option--active" : ""
                }`}
                onClick={() => choose(language)}
              >
                <img className="langselect__flag" src={`/flags/${language}.svg`} alt="" />
                <span>{LANGUAGE_NAMES[language]}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

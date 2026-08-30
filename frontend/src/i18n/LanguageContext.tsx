import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import type { LanguageChoice } from "../api/client";
import { MESSAGES, isRtl, resolveUiLanguage } from "./messages";
import type { Messages, UiLanguage } from "./messages";

const STORAGE_KEY = "artai.lang";

interface LanguageContextValue {
  choice: LanguageChoice;
  setChoice: (choice: LanguageChoice) => void;
  /** Переключает интерфейс между русским и английским. */
  toggleLanguage: () => void;
  uiLanguage: UiLanguage;
  t: Messages;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

function readStoredChoice(): LanguageChoice {
  const stored = localStorage.getItem(STORAGE_KEY);
  return (stored as LanguageChoice) ?? "auto";
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [choice, setChoiceState] = useState<LanguageChoice>(readStoredChoice);

  const setChoice = useCallback((next: LanguageChoice) => {
    setChoiceState(next);
    localStorage.setItem(STORAGE_KEY, next);
  }, []);

  const uiLanguage = useMemo(() => resolveUiLanguage(choice), [choice]);

  const toggleLanguage = useCallback(
    () => setChoice(resolveUiLanguage(choice) === "ru" ? "en" : "ru"),
    [choice, setChoice],
  );

  useEffect(() => {
    // Арабский разворачивает весь интерфейс.
    document.documentElement.lang = uiLanguage;
    document.documentElement.dir = isRtl(uiLanguage) ? "rtl" : "ltr";
  }, [uiLanguage]);

  const value = useMemo<LanguageContextValue>(
    () => ({ choice, setChoice, toggleLanguage, uiLanguage, t: MESSAGES[uiLanguage] }),
    [choice, setChoice, toggleLanguage, uiLanguage],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useI18n(): LanguageContextValue {
  const value = useContext(LanguageContext);
  if (!value) throw new Error("useI18n вызван вне LanguageProvider");
  return value;
}

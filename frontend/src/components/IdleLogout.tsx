import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { useI18n } from "../i18n/LanguageContext";
import { useIdleHolds } from "../lib/idle";
import { useDialog } from "./useDialog";

/**
 * Киоск в зале: гость отходит, не выйдя из учётки, и следующий тратит его генерации.
 * Поэтому после паузы показываем окно с обратным отсчётом, а по его истечении
 * выходим сами.
 */

// Двадцать секунд тишины — и окно с отсчётом ещё на пятнадцать: всего у гостя
// больше полуминуты, чтобы дать знать, что он никуда не ушёл.
const IDLE_MS = 20_000;
const COUNTDOWN_SECONDS = 15;

// Служебные почты выставки: с них работают сотрудники, и выбрасывать их незачем.
const IMMUNE_DOMAIN = "@ai.tavrida.art";

// Экран холста и админка живут сутками без прикосновений — там счётчик неуместен.
const UNWATCHED_PATHS = ["/dome", "/admin"];

// Скролл и колесо тоже считаем действием: на сенсорном киоске это основной жест.
const ACTIVITY_EVENTS = ["pointerdown", "pointermove", "keydown", "wheel", "touchstart", "scroll"];

export function isIdleImmune(email: string): boolean {
  return email.trim().toLowerCase().endsWith(IMMUNE_DOMAIN);
}

export default function IdleLogout() {
  const { access, signOut } = useAuth();
  const { pathname } = useLocation();
  const holds = useIdleHolds();
  const [warning, setWarning] = useState(false);

  const watched =
    access !== null && !isIdleImmune(access.email) && !UNWATCHED_PATHS.includes(pathname);

  // Учётка сменилась или гость ушёл со страницы киоска — предупреждение снимаем.
  useEffect(() => {
    if (!watched) setWarning(false);
  }, [watched]);

  useEffect(() => {
    if (!watched || warning || holds > 0) return;

    let timer = 0;
    const restart = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => setWarning(true), IDLE_MS);
    };

    restart();
    ACTIVITY_EVENTS.forEach((name) =>
      window.addEventListener(name, restart, { passive: true }),
    );

    return () => {
      window.clearTimeout(timer);
      ACTIVITY_EVENTS.forEach((name) => window.removeEventListener(name, restart));
    };
  }, [watched, warning, holds]);

  if (!watched || !warning) return null;

  return <IdleDialog onContinue={() => setWarning(false)} onExit={signOut} />;
}

function IdleDialog({ onContinue, onExit }: { onContinue: () => void; onExit: () => void }) {
  const { t } = useI18n();
  const navigate = useNavigate();
  const dialogRef = useRef<HTMLDivElement>(null);
  const continueButtonRef = useRef<HTMLButtonElement>(null);
  const [left, setLeft] = useState(COUNTDOWN_SECONDS);

  // «Продолжить» возвращает гостя на главный экран: сеанс продолжается с начала.
  const stay = useCallback(() => {
    onContinue();
    navigate("/");
  }, [onContinue, navigate]);

  const leave = useCallback(() => {
    onExit();
    navigate("/");
  }, [onExit, navigate]);

  // Esc — то же, что «Продолжить»: случайное касание клавиатуры не должно выкидывать.
  useDialog(dialogRef, stay);

  useEffect(() => {
    continueButtonRef.current?.focus();
  }, []);

  useEffect(() => {
    // Считаем от засечки, а не вычитанием по тику: фоновая вкладка тормозит таймеры.
    const deadline = Date.now() + COUNTDOWN_SECONDS * 1000;
    const timer = window.setInterval(() => {
      const rest = Math.ceil((deadline - Date.now()) / 1000);
      if (rest <= 0) {
        window.clearInterval(timer);
        leave();
      } else {
        setLeft(rest);
      }
    }, 250);

    return () => window.clearInterval(timer);
  }, [leave]);

  return (
    <div className="overlay">
      <div
        className="modal modal--idle"
        role="alertdialog"
        aria-modal="true"
        aria-label={t.idleTitle}
        ref={dialogRef}
      >
        <p className="idle__title">{t.idleTitle}</p>
        <p className="idle__countdown" aria-live="assertive">
          {left}
          <span className="idle__units">{t.secondsSuffix}</span>
        </p>

        <div className="modal__actions">
          <button type="button" className="btn btn--primary" onClick={stay} ref={continueButtonRef}>
            {t.idleContinue}
          </button>
          <button type="button" className="btn" onClick={leave}>
            {t.logout}
          </button>
        </div>
      </div>
    </div>
  );
}

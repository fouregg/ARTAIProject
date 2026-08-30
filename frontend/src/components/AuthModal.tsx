import { useEffect, useRef, useState } from "react";

import { useI18n } from "../i18n/LanguageContext";
import { REG } from "../i18n/registration";
import LoginForm from "./LoginForm";
import RegistrationForm from "./RegistrationForm";
import { useDialog } from "./useDialog";

export type AuthTab = "login" | "register";

interface Props {
  initialTab: AuthTab;
  onClose: () => void;
}

/** Вход и регистрация в одном окне: переключаемые вкладки, без ухода со страницы. */
export default function AuthModal({ initialTab, onClose }: Props) {
  const { t } = useI18n();
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const [tab, setTab] = useState<AuthTab>(initialTab);
  const [code, setCode] = useState("");
  const [hint, setHint] = useState<string | null>(null);

  useDialog(dialogRef, onClose);

  useEffect(() => {
    closeButtonRef.current?.focus();
  }, []);

  function switchTo(next: AuthTab) {
    setTab(next);
    setHint(null);
  }

  return (
    <div
      className="overlay"
      onMouseDown={(event) => event.target === event.currentTarget && onClose()}
    >
      <div
        className="modal modal--auth"
        role="dialog"
        aria-modal="true"
        aria-label={REG.authOpen}
        ref={dialogRef}
      >
        <button
          type="button"
          className="modal__close"
          onClick={onClose}
          aria-label={t.close}
          title={t.close}
          ref={closeButtonRef}
        >
          ×
        </button>

        <div className="tabs" role="tablist" aria-label={REG.authOpen}>
          <button
            type="button"
            role="tab"
            aria-selected={tab === "login"}
            className={`tabs__tab${tab === "login" ? " tabs__tab--active" : ""}`}
            onClick={() => switchTo("login")}
          >
            {REG.tabLogin}
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === "register"}
            className={`tabs__tab${tab === "register" ? " tabs__tab--active" : ""}`}
            onClick={() => switchTo("register")}
          >
            {REG.tabRegister}
          </button>
        </div>

        {/* Прокручивается только содержимое: вкладки и крестик всегда на виду. */}
        <div className="modal__body">
        {tab === "login" ? (
          <>
            <LoginForm
              onDone={onClose}
              onNeedsRegistration={(enteredCode) => {
                // Код настоящий, но анкеты по нему ещё нет — переносим его в регистрацию.
                setCode(enteredCode);
                setHint(REG.notRegistered);
                setTab("register");
              }}
            />
            <p className="authswitch">
              {REG.noAccount}{" "}
              <button type="button" className="linkbtn" onClick={() => switchTo("register")}>
                {REG.goRegister}
              </button>
            </p>
          </>
        ) : (
          <>
            <RegistrationForm initialCode={code} hint={hint} onDone={onClose} />
            <p className="authswitch">
              {REG.haveCode}{" "}
              <button type="button" className="linkbtn" onClick={() => switchTo("login")}>
                {REG.goLogin}
              </button>
            </p>
          </>
        )}
        </div>
      </div>
    </div>
  );
}

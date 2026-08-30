import { useState } from "react";

import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useI18n } from "../i18n/LanguageContext";
import { REG } from "../i18n/registration";

const CODE_LENGTH = 5;

interface Props {
  onDone: () => void;
  /** Код есть, но анкета не заполнена — уводим на вкладку регистрации. */
  onNeedsRegistration: (code: string) => void;
}

export default function LoginForm({ onDone, onNeedsRegistration }: Props) {
  const { t } = useI18n();
  const { signIn } = useAuth();

  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (busy || code.length !== CODE_LENGTH) return;

    setBusy(true);
    setError(null);
    try {
      const state = await signIn(code);
      if (state.registered) onDone();
      else onNeedsRegistration(code);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : String(caught));
      setCode("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="authform" onSubmit={handleSubmit}>
      <p className="stage__subtitle">{t.codeSubtitle}</p>

      <input
        className="field field--code"
        value={code}
        onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, CODE_LENGTH))}
        inputMode="numeric"
        autoComplete="off"
        autoFocus
        maxLength={CODE_LENGTH}
        placeholder="00000"
        aria-label={REG.codeLabel}
        disabled={busy}
      />

      <button
        type="submit"
        className="btn btn--primary btn--wide"
        disabled={busy || code.length !== CODE_LENGTH}
      >
        {busy ? t.signingIn : t.codeSubmit}
      </button>

      {error && <p className="error">{error}</p>}
    </form>
  );
}

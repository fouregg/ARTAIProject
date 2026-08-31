import { useState } from "react";

import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useI18n } from "../i18n/LanguageContext";
import { useReg } from "../i18n/registration";

interface Props {
  onDone: () => void;
  /** Почта известна, но анкеты по ней нет — уводим на вкладку регистрации. */
  onNeedsRegistration: (email: string) => void;
}

export default function LoginForm({ onDone, onNeedsRegistration }: Props) {
  const { t } = useI18n();
  const { signIn } = useAuth();
  const REG = useReg();

  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (busy || !email.includes("@")) return;

    setBusy(true);
    setError(null);
    try {
      const state = await signIn(email);
      if (state.registered) onDone();
      else onNeedsRegistration(email);
    } catch (caught) {
      // Незнакомой почты просто нет в базе. Это не ошибка гостя, а признак того,
      // что он здесь впервые — уводим на анкету, а не показываем красный текст.
      if (caught instanceof ApiError && caught.status === 401) {
        onNeedsRegistration(email);
        return;
      }
      setError(caught instanceof ApiError ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="authform" onSubmit={handleSubmit}>
      <p className="stage__subtitle">{t.codeSubtitle}</p>

      <input
        className="field field--email"
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        inputMode="email"
        autoComplete="email"
        autoFocus
        maxLength={255}
        placeholder="name@example.com"
        aria-label={REG.emailLabel}
        disabled={busy}
      />

      <button
        type="submit"
        className="btn btn--primary btn--wide"
        disabled={busy || !email.includes("@")}
      >
        {busy ? t.signingIn : t.codeSubmit}
      </button>

      {error && <p className="error">{error}</p>}
    </form>
  );
}

import { useEffect, useState } from "react";

import { ApiError } from "../api/client";
import { toAsciiDigits } from "../api/digits";
import type { LegalBundle } from "../api/client";
import { loadLegal } from "../api/legalCache";
import { useAuth } from "../auth/AuthContext";
import { useI18n } from "../i18n/LanguageContext";
import { useReg } from "../i18n/registration";

const ADULT_AGE = 18;
const CODE_LENGTH = 5;

function ageOn(birthDate: string, today: Date): number | null {
  const born = new Date(birthDate);
  if (Number.isNaN(born.getTime())) return null;

  let years = today.getFullYear() - born.getFullYear();
  const beforeBirthday =
    today.getMonth() < born.getMonth() ||
    (today.getMonth() === born.getMonth() && today.getDate() < born.getDate());
  if (beforeBirthday) years -= 1;
  return years;
}

interface Props {
  initialCode?: string;
  hint?: string | null;
  onDone: () => void;
}

/** Экран 1 терминала: код доступа, анкета участника и две обязательные отметки. */
export default function RegistrationForm({ initialCode = "", hint, onDone }: Props) {
  const { signUp } = useAuth();
  const { uiLanguage } = useI18n();
  const REG = useReg();

  const [legal, setLegal] = useState<LegalBundle | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [code, setCode] = useState(initialCode);
  const [lastName, setLastName] = useState("");
  const [firstName, setFirstName] = useState("");
  const [middleName, setMiddleName] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [country, setCountry] = useState("");

  const [acceptAgreement, setAcceptAgreement] = useState(false);
  const [acceptConsent, setAcceptConsent] = useState(false);
  const [isRepresentative, setIsRepresentative] = useState(false);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => setCode(initialCode), [initialCode]);

  useEffect(() => {
    let cancelled = false;
    loadLegal()
      .then((bundle) => !cancelled && setLegal(bundle))
      .catch(() => !cancelled && setLoadError(REG.loadFailed));
    return () => {
      cancelled = true;
    };
  }, []);

  const age = birthDate ? ageOn(birthDate, new Date()) : null;
  const minorNeedsRepresentative = age !== null && age < ADULT_AGE && !isRepresentative;

  const fieldsFilled =
    code.length === CODE_LENGTH &&
    lastName.trim() !== "" &&
    firstName.trim() !== "" &&
    birthDate !== "" &&
    country.trim() !== "";
  const consentsGiven = acceptAgreement && acceptConsent;
  const canSubmit = fieldsFilled && consentsGiven && !minorNeedsRepresentative && !busy;

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!legal || busy) return;

    if (!fieldsFilled) {
      setError(REG.required);
      return;
    }
    if (!consentsGiven) {
      setError(REG.checkboxesRequired);
      return;
    }
    // Пункты 11.2 и 11.5 Соглашения: за несовершеннолетнего отметку ставит представитель.
    if (minorNeedsRepresentative) {
      setError(legal.age_notice);
      return;
    }

    setBusy(true);
    setError(null);
    try {
      // Отправляем редакцию и хеш именно тех текстов, что были на экране (п. 12.1).
      await signUp(code, {
        last_name: lastName.trim(),
        first_name: firstName.trim(),
        middle_name: middleName.trim() || null,
        birth_date: birthDate,
        country: country.trim(),
        is_legal_representative: isRepresentative,
        accepted: legal.documents.map((document) => ({
          key: document.key,
          version: document.version,
          sha256: document.sha256,
        })),
        ui_language: uiLanguage,
      });
      onDone();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  }

  if (loadError) return <p className="error">{loadError}</p>;
  if (!legal) return <p className="stage__subtitle">{REG.loading}</p>;

  const agreement = legal.documents.find((document) => document.key === "agreement");
  const consent = legal.documents.find((document) => document.key === "consent");

  return (
    <form className="authform" onSubmit={handleSubmit}>
      {hint && <p className="notice">{hint}</p>}

      <label className="control">
        <span>
          {REG.codeLabel} * <span className="control__hint">{REG.codeHint}</span>
        </span>
        <input
          className="field field--code field--code-inline"
          value={code}
          onChange={(event) =>
            setCode(toAsciiDigits(event.target.value).slice(0, CODE_LENGTH))
          }
          inputMode="numeric"
          autoComplete="off"
          maxLength={CODE_LENGTH}
          placeholder="00000"
          disabled={busy}
        />
      </label>

      <div className="registration__grid">
        <label className="control">
          <span>{REG.lastName} *</span>
          <input className="field" value={lastName} onChange={(e) => setLastName(e.target.value)} maxLength={120} disabled={busy} />
        </label>
        <label className="control">
          <span>{REG.firstName} *</span>
          <input className="field" value={firstName} onChange={(e) => setFirstName(e.target.value)} maxLength={120} disabled={busy} />
        </label>
        <label className="control">
          <span>{REG.middleName}</span>
          <input className="field" value={middleName} onChange={(e) => setMiddleName(e.target.value)} maxLength={120} disabled={busy} />
        </label>
        <label className="control">
          <span>{REG.birthDate} *</span>
          <input className="field" type="date" value={birthDate} onChange={(e) => setBirthDate(e.target.value)} disabled={busy} />
        </label>
        <label className="control">
          <span>{REG.country} *</span>
          <input className="field" value={country} onChange={(e) => setCountry(e.target.value)} maxLength={120} disabled={busy} />
        </label>
      </div>

      <p className="notice">{legal.age_notice}</p>

      <label className="check">
        <input
          type="checkbox"
          checked={acceptAgreement}
          onChange={(e) => setAcceptAgreement(e.target.checked)}
          disabled={busy}
        />
        <span>{legal.checkbox_agreement}</span>
      </label>
      {agreement && (
        <details className="legal">
          <summary>{REG.agreementFull}</summary>
          <pre className="legal__text">{agreement.text}</pre>
        </details>
      )}

      <label className="check">
        <input
          type="checkbox"
          checked={acceptConsent}
          onChange={(e) => setAcceptConsent(e.target.checked)}
          disabled={busy}
        />
        <span>{legal.checkbox_consent}</span>
      </label>
      {consent && (
        <details className="legal">
          <summary>{REG.consentFull}</summary>
          <pre className="legal__text">{consent.text}</pre>
        </details>
      )}

      <label className="check">
        <input
          type="checkbox"
          checked={isRepresentative}
          onChange={(e) => setIsRepresentative(e.target.checked)}
          disabled={busy}
        />
        <span>{REG.representative}</span>
      </label>

      <a className="legal__link" href={legal.policy_url} target="_blank" rel="noreferrer">
        {REG.policy}
      </a>

      <button type="submit" className="btn btn--primary btn--wide" disabled={!canSubmit}>
        {busy ? REG.submitting : REG.registerSubmit}
      </button>

      {minorNeedsRepresentative && <p className="error">{legal.age_notice}</p>}
      {error && <p className="error">{error}</p>}
    </form>
  );
}

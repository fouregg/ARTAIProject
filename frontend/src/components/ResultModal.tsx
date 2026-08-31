import { useEffect, useRef, useState } from "react";

import { ApiError, displayOnDome, saveToGallery } from "../api/client";
import type { Generation } from "../api/client";
import { useLegal } from "../api/legalCache";
import { useI18n } from "../i18n/LanguageContext";
import { useDialog } from "./useDialog";

interface Props {
  generation: Generation;
  regenerating: boolean;
  elapsedSeconds: number;
  canRegenerate: boolean;
  onRegenerate: () => void;
  onEditPrompt: () => void;
  onClose: () => void;
}

export default function ResultModal({
  generation,
  regenerating,
  elapsedSeconds,
  canRegenerate,
  onRegenerate,
  onEditPrompt,
  onClose,
}: Props) {
  const { t, uiLanguage } = useI18n();
  const legal = useLegal();
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const [saved, setSaved] = useState(false);
  const [savePending, setSavePending] = useState(false);
  const [displayed, setDisplayed] = useState(false);
  const [displayPending, setDisplayPending] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Новая картинка — действия снова доступны.
  useEffect(() => {
    setSaved(false);
    setDisplayed(false);
    setActionError(null);
  }, [generation.id]);

  useEffect(() => {
    closeButtonRef.current?.focus();
  }, []);

  useDialog(dialogRef, onClose);

  const expiresAtLabel = new Date(generation.expires_at).toLocaleTimeString(uiLanguage, {
    hour: "2-digit",
    minute: "2-digit",
  });

  async function handleSave() {
    setSavePending(true);
    setActionError(null);
    try {
      await saveToGallery(generation.id);
      setSaved(true);
    } catch (error) {
      setActionError(error instanceof ApiError ? error.message : String(error));
    } finally {
      setSavePending(false);
    }
  }

  async function handleDisplay() {
    setDisplayPending(true);
    setActionError(null);
    try {
      await displayOnDome(generation.id);
      setDisplayed(true);
    } catch (error) {
      setActionError(error instanceof ApiError ? error.message : String(error));
    } finally {
      setDisplayPending(false);
    }
  }

  return (
    <div className="overlay" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={t.title} ref={dialogRef}>
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

        <div className="modal__image">
          <img src={generation.url} alt={generation.prompt_original} />
          {regenerating && (
            <div className="modal__spinner">
              <span className="spinner" />
              <span>
                {t.stageGenerating} · {elapsedSeconds}&nbsp;{t.secondsSuffix}
              </span>
              <span className="modal__spinner-hint">{t.takesUpTo}</span>
            </div>
          )}
        </div>

        {/* Обязательная маркировка результата (п. 10.2 Соглашения). */}
        {legal && <p className="disclosure">{legal.ai_disclosure}</p>}

        <div className="modal__meta">
          <p className="modal__prompt" dir="auto">
            {generation.prompt_original}
          </p>
          {generation.detected_lang && (
            <p className="modal__hint">
              {t.detectedAs}: <strong>{generation.detected_lang}</strong>
            </p>
          )}
          {generation.translation_degraded && <p className="modal__warning">{t.degraded}</p>}
          {/* Незакреплённая картинка живёт ограниченное время — предупреждаем заранее. */}
          {!saved && !displayed && (
            <p className="modal__hint modal__hint--ttl">
              {t.ttlHint.replace("{time}", expiresAtLabel)}
            </p>
          )}
          {actionError && <p className="modal__warning">{actionError}</p>}
        </div>

        <div className="modal__actions">
          <button type="button" className="btn btn--primary" onClick={onRegenerate} disabled={regenerating || !canRegenerate}>
            {t.again}
          </button>
          <button
            type="button"
            className="btn"
            onClick={handleSave}
            disabled={saved || savePending || regenerating}
          >
            {saved ? t.saved : t.save}
          </button>
          <button
            type="button"
            className="btn"
            onClick={handleDisplay}
            disabled={displayed || displayPending || regenerating}
          >
            {displayed ? t.displayed : t.display}
          </button>
          <button type="button" className="btn" onClick={onEditPrompt} disabled={regenerating}>
            {t.editPrompt}
          </button>
        </div>
      </div>
    </div>
  );
}

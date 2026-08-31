import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError, startGeneration, waitForGeneration } from "../api/client";
import type { Generation, JobStage } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import AuthModal from "../components/AuthModal";
import type { AuthTab } from "../components/AuthModal";
import { BrandFooter, EventLogo } from "../components/BrandMarks";
import CanvasPreview from "../components/CanvasPreview";
import LanguageSelect from "../components/LanguageSelect";
import ResultModal from "../components/ResultModal";
import { useI18n } from "../i18n/LanguageContext";
import { useReg } from "../i18n/registration";

// Формат и качество больше не выбираются: квадрат и low для всех.
// low заметно быстрее medium — на киоске очередь важнее детализации.
const ASPECT_RATIO = "1:1";
const QUALITY = "low";

export default function PromptPage() {
  const { t } = useI18n();
  const REG = useReg();
  const { access, signOut, refresh } = useAuth();

  const [prompt, setPrompt] = useState("");
  const [stage, setStage] = useState<JobStage | null>(null);
  const [busy, setBusy] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [generation, setGeneration] = useState<Generation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [authTab, setAuthTab] = useState<AuthTab | null>(null);
  const [authNotice, setAuthNotice] = useState<string | null>(null);
  const promptRef = useRef<HTMLTextAreaElement>(null);

  // Экран ввода открыт всем; код спрашиваем только в момент отправки запроса.
  const authorized = access !== null && access.registered;
  const exhausted = authorized && access.remaining <= 0;

  const stageLabel: Record<JobStage, string> = {
    queued: t.stageQueued,
    checking: t.stageChecking,
    translating: t.stageTranslating,
    generating: t.stageGenerating,
    done: t.stageGenerating,
    error: t.errorTitle,
  };

  // Модель рисует до полутора минут. Без бегущего счётчика статичная надпись
  // выглядит как зависший интерфейс, поэтому показываем, что время идёт.
  const working = busy || regenerating;
  useEffect(() => {
    if (!working) {
      setElapsed(0);
      return;
    }
    const startedAt = Date.now();
    setElapsed(0);
    const timer = window.setInterval(
      () => setElapsed(Math.round((Date.now() - startedAt) / 1000)),
      1000,
    );
    return () => window.clearInterval(timer);
  }, [working]);

  async function runGeneration(params: {
    prompt: string;
    skipTranslation: boolean;
    originalPrompt?: string;
    lang?: "auto" | "en";
  }): Promise<Generation> {
    const { job_id } = await startGeneration({
      prompt: params.prompt,
      lang: params.lang ?? "auto",
      aspect_ratio: ASPECT_RATIO,
      quality: QUALITY,
      skip_translation: params.skipTranslation,
      original_prompt: params.originalPrompt,
    });
    return waitForGeneration(job_id, setStage);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (busy || exhausted) return;

    if (!authorized) {
      setAuthNotice(REG.needAuth);
      setAuthTab(access ? "register" : "login");
      return;
    }

    const text = prompt.trim();
    if (!text) {
      setError(t.emptyPrompt);
      return;
    }

    setBusy(true);
    setError(null);
    setAuthNotice(null);
    setStage("queued");
    try {
      setGeneration(await runGeneration({ prompt: text, skipTranslation: false }));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : String(caught));
    } finally {
      setBusy(false);
      setStage(null);
      // Счётчик оставшихся генераций обновляем в любом случае: попытка потрачена.
      await refresh();
    }
  }

  async function handleRegenerate() {
    if (!generation || regenerating || exhausted) return;

    setRegenerating(true);
    setError(null);
    try {
      // Промпт уже на английском — перевод не повторяем, экономим вызов модели.
      // Исходный текст пользователя передаём отдельно: он остаётся и в журнале, и в модалке.
      setGeneration(
        await runGeneration({
          prompt: generation.prompt_translated ?? generation.prompt_original,
          originalPrompt: generation.prompt_original,
          lang: "en",
          skipTranslation: true,
        }),
      );
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : String(caught));
    } finally {
      setRegenerating(false);
      setStage(null);
      await refresh();
    }
  }

  return (
    <div className="stage">
      <header className="topbar">
        <EventLogo />

        <div className="topbar__actions">
          <LanguageSelect />

          {/* Галерея — только для вошедших: гостю там смотреть нечего. */}
          {authorized && (
            <Link className="btn btn--ghost btn--small" to="/gallery">
              {t.gallery}
            </Link>
          )}
          {authorized ? (
            <>
              <span className="topbar__counter">
                {t.remaining.replace("{n}", String(access?.remaining ?? 0))}
              </span>
              <button type="button" className="btn btn--ghost btn--small" onClick={signOut}>
                {t.logout}
              </button>
            </>
          ) : (
            <button
              type="button"
              className="btn btn--small"
              onClick={() => setAuthTab(access ? "register" : "login")}
            >
              {REG.authOpen}
            </button>
          )}
        </div>
      </header>

      <form className="stage__form" onSubmit={handleSubmit}>
        <h1 className="stage__title">{t.title}</h1>
        <p className="stage__subtitle">{t.subtitle}</p>

        <textarea
          className="field field--prompt"
          ref={promptRef}
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder={t.placeholder}
          maxLength={2000}
          rows={4}
          autoFocus
          // Гость может писать на арабском — направление текста определяем по содержимому.
          dir="auto"
          disabled={busy || exhausted}
          onKeyDown={(event) => {
            // Enter отправляет, Shift+Enter переносит строку — привычно для поля запроса.
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void handleSubmit(event);
            }
          }}
        />

        <button
          type="submit"
          className="btn btn--primary btn--wide"
          disabled={busy || exhausted}
        >
          {busy && stage ? stageLabel[stage] : t.generate}
        </button>

        {busy && (
          <div className="progress">
            <span className="spinner" />
            <div className="progress__text">
              <span>
                {stage ? stageLabel[stage] : t.stageQueued} · {elapsed}&nbsp;{t.secondsSuffix}
              </span>
              <span className="progress__hint">{t.takesUpTo}</span>
            </div>
          </div>
        )}

        {authNotice && <p className="notice">{authNotice}</p>}

        {exhausted && <p className="error">{t.exhausted}</p>}

        {error && (
          <p className="error">
            <strong>{t.errorTitle}:</strong> {error}
          </p>
        )}
      </form>

      <CanvasPreview />

      <BrandFooter />

      {authTab && (
        <AuthModal
          initialTab={authTab}
          onClose={() => {
            setAuthTab(null);
            setAuthNotice(null);
          }}
        />
      )}

      {generation && (
        <ResultModal
          generation={generation}
          regenerating={regenerating}
          elapsedSeconds={elapsed}
          canRegenerate={!exhausted}
          onRegenerate={handleRegenerate}
          onEditPrompt={() => {
            // Текст запроса из поля не стирается, поэтому достаточно вернуть в него курсор.
            setGeneration(null);
            window.setTimeout(() => promptRef.current?.focus(), 0);
          }}
          onClose={() => setGeneration(null)}
        />
      )}
    </div>
  );
}

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import {
  ApiError,
  clearDome,
  fetchAdminDome,
  fetchAdminStats,
  hideDomeItem,
  restoreDomeItem,
} from "../api/client";
import type { AdminDomeItem, AdminStats } from "../api/client";

/**
 * Модерация цифрового холста: /admin?token=<ADMIN_TOKEN>.
 *
 * Снятие мягкое — плитка гаснет на холсте, но запись остаётся и её можно вернуть.
 * Так безопаснее на живой инсталляции: промах кнопкой не теряет работу участника.
 */
export default function AdminPage() {
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";

  const [items, setItems] = useState<AdminDomeItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [statsOpen, setStatsOpen] = useState(false);

  const load = useCallback(async () => {
    try {
      setItems(await fetchAdminDome(token));
      setError(null);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : String(caught));
      setItems([]);
    }
  }, [token]);

  useEffect(() => {
    if (token) void load();
  }, [token, load]);

  // Цифры запрашиваем на каждое открытие: сутки — окно скользящее, кешировать нечего.
  async function toggleStats() {
    if (statsOpen) {
      setStatsOpen(false);
      return;
    }

    setStatsOpen(true);
    setError(null);
    try {
      setStats(await fetchAdminStats(token));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : String(caught));
      setStatsOpen(false);
    }
  }

  async function act(id: number, action: () => Promise<unknown>) {
    setBusyId(id);
    setError(null);
    try {
      await action();
      await load();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : String(caught));
    } finally {
      setBusyId(null);
    }
  }

  async function handleClear() {
    if (!window.confirm("Убрать с холста все изображения? Записи сохранятся, их можно вернуть."))
      return;

    setError(null);
    try {
      await clearDome(token);
      await load();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : String(caught));
    }
  }

  if (!token) {
    return (
      <div className="page">
        <p className="error">Нужен адрес вида /admin?token=&lt;ADMIN_TOKEN&gt;</p>
      </div>
    );
  }

  const visible = (items ?? []).filter((item) => item.is_visible);
  const hidden = (items ?? []).filter((item) => !item.is_visible);

  return (
    <div className="page">
      <header className="page__header">
        <h1>Цифровой холст</h1>
        <div className="topbar__actions">
          <button type="button" className="btn btn--ghost btn--small" onClick={() => void load()}>
            Обновить
          </button>
          <button
            type="button"
            className="btn btn--ghost btn--small"
            onClick={() => void toggleStats()}
            aria-expanded={statsOpen}
          >
            Статистика
          </button>
          <button
            type="button"
            className="btn btn--small"
            onClick={handleClear}
            disabled={visible.length === 0}
          >
            Очистить холст
          </button>
        </div>
      </header>

      {error && <p className="error">{error}</p>}

      {statsOpen && stats && (
        <section className="stats">
          <h2 className="stats__total">
            Регистраций за сутки: <strong>{stats.total}</strong>
          </h2>
          <p className="stats__period">
            С {new Date(stats.since).toLocaleString("ru")} по настоящий момент
          </p>

          {stats.total === 0 ? (
            <p className="page__subtitle">За эти сутки никто не регистрировался</p>
          ) : (
            <div className="stats__grid">
              <div className="stats__block">
                <h3 className="stats__heading">По странам</h3>
                <table className="stats__table">
                  <tbody>
                    {stats.by_country.map((row) => (
                      <tr key={row.country}>
                        <td>{row.country}</td>
                        <td>{row.count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="stats__block">
                <h3 className="stats__heading">По возрасту</h3>
                <table className="stats__table">
                  <tbody>
                    <tr>
                      <td>До 18</td>
                      <td>{stats.under_18}</td>
                    </tr>
                    <tr>
                      <td>18–35</td>
                      <td>{stats.from_18_to_35}</td>
                    </tr>
                    <tr>
                      <td>35+</td>
                      <td>{stats.over_35}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </section>
      )}

      <p className="page__subtitle">
        На холсте {visible.length}, скрыто {hidden.length}
      </p>

      <div className="gallery">
        {visible.map((item) => (
          <figure className="gallery__item" key={item.id}>
            <img src={item.thumb_url} alt={item.prompt_original} loading="lazy" />
            <figcaption>
              <span title={item.prompt_original}>{item.prompt_original}</span>
              <button
                type="button"
                className="btn btn--small"
                onClick={() => void act(item.id, () => hideDomeItem(token, item.id))}
                disabled={busyId === item.id}
              >
                Убрать
              </button>
            </figcaption>
          </figure>
        ))}
      </div>

      {visible.length === 0 && items !== null && (
        <p className="page__subtitle">На холсте пока пусто</p>
      )}

      {hidden.length > 0 && (
        <details className="legal">
          <summary>Скрытые ({hidden.length})</summary>
          <div className="gallery">
            {hidden.map((item) => (
              <figure className="gallery__item gallery__item--hidden" key={item.id}>
                <img src={item.thumb_url} alt={item.prompt_original} loading="lazy" />
                <figcaption>
                  <span title={item.prompt_original}>{item.prompt_original}</span>
                  <button
                    type="button"
                    className="btn btn--small"
                    onClick={() => void act(item.id, () => restoreDomeItem(token, item.id))}
                    disabled={busyId === item.id}
                  >
                    Вернуть
                  </button>
                </figcaption>
              </figure>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}

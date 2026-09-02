import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";

import { ApiError, deleteGalleryItem, displayOnDome, fetchGallery } from "../api/client";
import type { GalleryItem } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { BrandFooter, EventLogo } from "../components/BrandMarks";
import { useI18n } from "../i18n/LanguageContext";

export default function GalleryPage() {
  const { t } = useI18n();
  const { access, checking } = useAuth();
  const [items, setItems] = useState<GalleryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sendingId, setSendingId] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchGallery()
      .then((data) => !cancelled && setItems(data))
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof ApiError ? caught.message : String(caught));
          setItems([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleDisplay(item: GalleryItem) {
    setSendingId(item.id);
    setError(null);
    try {
      await displayOnDome(item.generation_id);
      // Отмечаем локально: перезапрашивать весь список ради одного флага незачем.
      setItems((current) =>
        (current ?? []).map((row) => (row.id === item.id ? { ...row, on_canvas: true } : row)),
      );
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : String(caught));
    } finally {
      setSendingId(null);
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteGalleryItem(id);
      setItems((current) => (current ?? []).filter((item) => item.id !== id));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : String(caught));
    }
  }

  // Прямой заход по адресу без кода тоже возвращаем на экран ввода.
  if (checking) return <div className="page" />;
  if (!access?.registered) return <Navigate to="/" replace />;

  return (
    <div className="page">
      <header className="page__header">
        <EventLogo />
        <Link className="btn btn--ghost btn--small" to="/">
          {t.back}
        </Link>
      </header>

      <h1>{t.galleryTitle}</h1>

      {error && (
        <p className="error">
          <strong>{t.errorTitle}:</strong> {error}
        </p>
      )}

      {items !== null && items.length === 0 && <p className="page__subtitle">{t.galleryEmpty}</p>}

      <div className="gallery">
        {(items ?? []).map((item) => (
          <figure className="gallery__item" key={item.id}>
            <img src={item.thumb_url} alt={item.prompt_original} loading="lazy" />
            <figcaption>
              <span title={item.prompt_original}>{item.prompt_original}</span>
              <div className="gallery__actions">
                <button
                  type="button"
                  className="btn btn--small btn--primary"
                  onClick={() => void handleDisplay(item)}
                  disabled={item.on_canvas || sendingId === item.id}
                >
                  {item.on_canvas ? t.displayed : t.display}
                </button>
                <button
                  type="button"
                  className="btn btn--small"
                  onClick={() => void handleDelete(item.id)}
                >
                  {t.delete}
                </button>
              </div>
            </figcaption>
          </figure>
        ))}
      </div>

      <BrandFooter />
    </div>
  );
}

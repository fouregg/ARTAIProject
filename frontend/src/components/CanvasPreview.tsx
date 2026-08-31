import { useEffect, useMemo, useState } from "react";

import { fetchDomePreview } from "../api/client";
import type { DomePreview } from "../api/client";
import { useI18n } from "../i18n/LanguageContext";
import { splitIntoRows } from "../lib/collage";

// Холст меняет страницу раз в минуту; опрашиваем чаще, чтобы миниатюра не отставала.
const REFRESH_MS = 15000;
const PREVIEW_RATIO = 16 / 9;

/** Мини-полотно: что прямо сейчас показывает цифровой холст в зале. */
export default function CanvasPreview() {
  const { t } = useI18n();
  const [preview, setPreview] = useState<DomePreview | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await fetchDomePreview();
        if (!cancelled) setPreview(data);
      } catch {
        // Холст недоступен — просто не показываем миниатюру, экран ввода важнее.
      }
    }

    void load();
    const timer = window.setInterval(load, REFRESH_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  const rows = useMemo(() => {
    if (!preview) return [];
    // Та же раскладка, что на самом холсте, только в пропорциях миниатюры.
    const sizes = splitIntoRows(preview.items.length, PREVIEW_RATIO, 1);
    const result: DomePreview["items"][] = [];
    let offset = 0;
    for (const size of sizes) {
      result.push(preview.items.slice(offset, offset + size));
      offset += size;
    }
    return result;
  }, [preview]);

  if (!preview || preview.items.length === 0) return null;

  return (
    <section className="canvasview">
      <header className="canvasview__header">
        <span>{t.canvasNow}</span>
        <span className="canvasview__page">
          {t.canvasPage
            .replace("{n}", String(preview.page))
            .replace("{m}", String(preview.page_count))}
        </span>
      </header>

      <div className="canvasview__frame">
        {rows.map((row, index) => (
          <div className="canvasview__row" key={index}>
            {row.map((item) => (
              <div className="canvasview__tile" key={item.id}>
                <img src={item.thumb_url} alt="" loading="lazy" />
              </div>
            ))}
          </div>
        ))}
      </div>
    </section>
  );
}

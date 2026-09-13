import { useEffect, useMemo, useState } from "react";

import { fetchDomePreview } from "../api/client";
import type { DomePreview } from "../api/client";
import { useI18n } from "../i18n/LanguageContext";
import { splitIntoRows } from "../lib/collage";

// Холст меняет страницу не чаще раза в минуту; опрашиваем чаще, чтобы миниатюра не отставала.
const REFRESH_MS = 15000;
// Запасные пропорции, если сервер почему-то не прислал свои.
const FALLBACK_ASPECT = { width: 9, height: 16 };

/** «9:16» -> {width: 9, height: 16}. Мусор в настройке не должен ломать экран ввода. */
function parseAspect(raw: string | undefined) {
  const [width, height] = (raw ?? "").split(":").map(Number);
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
    return FALLBACK_ASPECT;
  }
  return { width, height };
}

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

  const aspect = parseAspect(preview?.aspect);

  const rows = useMemo(() => {
    if (!preview) return [];
    // Та же раскладка, что на самом холсте, и в тех же пропорциях: миниатюра должна
    // показывать ровно то, что видно на стене, а стена книжная.
    const sizes = splitIntoRows(preview.items.length, aspect.width, aspect.height);
    const result: DomePreview["items"][] = [];
    let offset = 0;
    for (const size of sizes) {
      result.push(preview.items.slice(offset, offset + size));
      offset += size;
    }
    return result;
  }, [preview, aspect.width, aspect.height]);

  if (!preview || preview.items.length === 0) return null;

  return (
    <section className={`canvasview${aspect.height > aspect.width ? " canvasview--portrait" : ""}`}>
      <header className="canvasview__header">
        <span>{t.canvasNow}</span>
        <span className="canvasview__page">
          {t.canvasPage
            .replace("{n}", String(preview.page))
            .replace("{m}", String(preview.page_count))}
        </span>
      </header>

      <div
        className="canvasview__frame"
        style={{ aspectRatio: `${aspect.width} / ${aspect.height}` }}
      >
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

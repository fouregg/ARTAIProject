import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { domeSocketUrl, fetchDomeItems } from "../api/client";
import type { DomeItem } from "../api/client";
import { useLegal } from "../api/legalCache";

type ConnectionState = "connecting" | "online" | "offline" | "unauthorized";

const MAX_RECONNECT_DELAY_MS = 15000;
// Пока сокет не поднялся, коллаж добираем обычными запросами.
const POLL_INTERVAL_MS = 10000;

// К концу фестиваля изображений будут тысячи. Показывать их одним полотном нельзя:
// плитка выродится в точку, а браузер задохнётся от количества картинок. Поэтому
// холст листает страницы по 50 штук, меняя их раз в минуту.
const PAGE_SIZE = 50;
const PAGE_INTERVAL_MS = 60000;

/**
 * Раскладка коллажа: строками, а не жёсткой сеткой.
 *
 * Сетка repeat(N, 1fr) оставляет чёрные дыры, когда число картинок не делится
 * на число колонок. Здесь строки заполняются целиком при любом количестве плиток,
 * а число строк подбирается под пропорции экрана, чтобы плитки не вытягивались.
 */
function splitIntoRows(count: number, width: number, height: number): number[] {
  if (count === 0) return [];

  const rows = Math.max(1, Math.round(Math.sqrt((count * height) / Math.max(width, 1))));
  const base = Math.floor(count / rows);
  let extra = count % rows;

  return Array.from({ length: rows }, () => {
    const size = base + (extra > 0 ? 1 : 0);
    if (extra > 0) extra -= 1;
    return size;
  }).filter((size) => size > 0);
}

/**
 * Экран купола. Открывается на отдельном устройстве в киоск-режиме:
 *   https://<домен>/dome?token=<DOME_TOKEN>
 * Живёт сутками без присмотра, поэтому переподключается сам и после разрыва
 * заново получает снапшот коллажа.
 */
export default function DomePage() {
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const legal = useLegal();

  const [items, setItems] = useState<DomeItem[]>([]);
  const [page, setPage] = useState(0);
  const [connection, setConnection] = useState<ConnectionState>("connecting");
  const [viewport, setViewport] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });

  const socketRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);
  const timerRef = useRef<number | null>(null);
  const closedByUsRef = useRef(false);

  useEffect(() => {
    function onResize() {
      setViewport({ width: window.innerWidth, height: window.innerHeight });
    }
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    if (!token) {
      setConnection("unauthorized");
      return;
    }

    closedByUsRef.current = false;

    function scheduleReconnect() {
      // Экспоненциальная задержка: 1с, 2с, 4с … но не дольше 15 секунд.
      const delay = Math.min(2 ** retryRef.current * 1000, MAX_RECONNECT_DELAY_MS);
      retryRef.current += 1;
      timerRef.current = window.setTimeout(connect, delay);
    }

    function connect() {
      let socket: WebSocket;
      try {
        socket = new WebSocket(domeSocketUrl(token));
      } catch {
        // Конструктор бросает, если сокеты запрещены политикой браузера или прокси.
        // Роняться нельзя: экран должен остаться на экране и добирать картинки по HTTP.
        setConnection("offline");
        scheduleReconnect();
        return;
      }
      socketRef.current = socket;

      socket.onopen = () => {
        retryRef.current = 0;
        setConnection("online");
      };

      socket.onmessage = (event) => {
        const message = JSON.parse(event.data as string);
        switch (message.type) {
          case "snapshot":
            setItems(message.items as DomeItem[]);
            break;
          case "image_added":
            setItems((current) =>
              current.some((item) => item.id === (message.item as DomeItem).id)
                ? current
                : [...current, message.item as DomeItem],
            );
            break;
          case "image_removed":
            // Модератор снял плитку — гасим её сразу, не дожидаясь опроса.
            setItems((current) => current.filter((item) => item.id !== message.id));
            break;
          case "cleared":
            setItems([]);
            break;
          default:
            break; // ping и всё неизвестное игнорируем
        }
      };

      socket.onclose = (event) => {
        if (closedByUsRef.current) return;
        if (event.code === 4401) {
          setConnection("unauthorized");
          return;
        }

        setConnection("offline");
        scheduleReconnect();
      };

      socket.onerror = () => socket.close();
    }

    connect();

    return () => {
      closedByUsRef.current = true;
      if (timerRef.current !== null) window.clearTimeout(timerRef.current);
      socketRef.current?.close();
    };
  }, [token]);

  // Запасной канал. На площадке сеть может резать апгрейд до WebSocket — тогда экран
  // остался бы пустым и незаметно. Пока сокет не в строю, тянем снапшот по HTTP:
  // обычный GET проходит везде, где вообще работает интернет.
  useEffect(() => {
    if (!token || connection === "online" || connection === "unauthorized") return;

    let cancelled = false;
    async function poll() {
      try {
        const snapshot = await fetchDomeItems(token);
        if (!cancelled) setItems(snapshot);
      } catch {
        // Сеть моргнула — следующий тик попробует снова.
      }
    }

    poll();
    const timer = window.setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [token, connection]);

  const pageCount = Math.max(1, Math.ceil(items.length / PAGE_SIZE));

  // Картинки убрали — текущая страница могла оказаться за концом списка.
  useEffect(() => {
    if (page >= pageCount) setPage(0);
  }, [page, pageCount]);

  // Перелистывание. Пока страница одна, таймер не нужен.
  useEffect(() => {
    if (pageCount < 2) return;

    const timer = window.setInterval(
      () => setPage((current) => (current + 1) % pageCount),
      PAGE_INTERVAL_MS,
    );
    return () => window.clearInterval(timer);
  }, [pageCount]);

  const pageItems = useMemo(
    () => items.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE),
    [items, page],
  );

  const rows = useMemo(() => {
    const sizes = splitIntoRows(pageItems.length, viewport.width, viewport.height);
    const result: DomeItem[][] = [];
    let offset = 0;
    for (const size of sizes) {
      result.push(pageItems.slice(offset, offset + size));
      offset += size;
    }
    return result;
  }, [pageItems, viewport.width, viewport.height]);

  return (
    <div className="dome">
      {connection !== "online" && (
        <div className="dome__status" data-state={connection}>
          {connection === "unauthorized"
            ? "Нужен корректный ?token= в адресе экрана"
            : connection === "connecting"
              ? "Подключение…"
              : "Прямой канал недоступен, обновляем список запросами"}
        </div>
      )}

      {items.length === 0 && connection === "online" && (
        <div className="dome__empty">Ожидание изображений…</div>
      )}

      {/* Маркировка обязательна и на экспозиционном экране. */}
      {items.length > 0 && (
        <div className="dome__disclosure">
          {legal && <span>{legal.ai_disclosure}</span>}
          {pageCount > 1 && (
            <span className="dome__page">
              Страница {page + 1} из {pageCount}
            </span>
          )}
        </div>
      )}

      <div className="dome__collage">
        {rows.map((row, index) => (
          <div className="dome__row" key={`${page}-${index}`}>
            {row.map((item) => (
              <div className="dome__tile" key={item.id}>
                <img src={item.thumb_url} alt="" />
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

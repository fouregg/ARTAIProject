import { useSyncExternalStore } from "react";

/**
 * Пауза для счётчика бездействия.
 *
 * Гость считается бездействующим по событиям мыши и клавиатуры, но модель рисует
 * до полутора минут, и всё это время человек просто смотрит на экран. Без паузы
 * окно выхода выскакивало бы поверх почти готовой картинки, поэтому на время
 * долгих операций счётчик замирает.
 */

let holds = 0;
const listeners = new Set<() => void>();

/** Взять паузу. Возвращённая функция снимает её — годится как cleanup эффекта. */
export function holdIdle(): () => void {
  holds += 1;
  listeners.forEach((listener) => listener());

  let released = false;
  return () => {
    if (released) return;
    released = true;
    holds -= 1;
    listeners.forEach((listener) => listener());
  };
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function snapshot(): number {
  return holds;
}

/** Сколько пауз держат счётчик прямо сейчас. Ноль — можно отсчитывать бездействие. */
export function useIdleHolds(): number {
  return useSyncExternalStore(subscribe, snapshot, snapshot);
}

import { useEffect } from "react";
import type { RefObject } from "react";

// Поля ввода тоже участвуют в обходе: в модалке входа фокус должен доходить до них.
const FOCUSABLE =
  'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), ' +
  'textarea:not([disabled]), summary, [tabindex]:not([tabindex="-1"])';

/**
 * Общее поведение модального окна: закрытие по Esc и фокус, запертый внутри диалога.
 * Один хук на все модалки, чтобы клавиатурная навигация везде вела себя одинаково.
 */
export function useDialog(ref: RefObject<HTMLElement>, onClose: () => void): void {
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
        return;
      }
      if (event.key !== "Tab" || !ref.current) return;

      const items = Array.from(ref.current.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
        (item) => item.offsetParent !== null,
      );
      if (items.length === 0) return;

      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [ref, onClose]);
}

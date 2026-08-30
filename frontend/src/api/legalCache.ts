import { useEffect, useState } from "react";

import { fetchLegal } from "./client";
import type { LegalBundle } from "./client";

// Тексты не меняются в течение сессии, поэтому запрашиваем их один раз на вкладку.
let pending: Promise<LegalBundle> | null = null;

export function loadLegal(): Promise<LegalBundle> {
  pending ??= fetchLegal().catch((error) => {
    pending = null; // сеть моргнула — дадим следующему вызову попробовать снова
    throw error;
  });
  return pending;
}

export function useLegal(): LegalBundle | null {
  const [bundle, setBundle] = useState<LegalBundle | null>(null);

  useEffect(() => {
    let cancelled = false;
    loadLegal()
      .then((value) => !cancelled && setBundle(value))
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  return bundle;
}

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import {
  ApiError,
  fetchAccessState,
  getStoredEmail,
  login as loginRequest,
  register as registerRequest,
  storeEmail,
} from "../api/client";
import type { AccessState, RegisterParams } from "../api/client";

interface AuthContextValue {
  access: AccessState | null;
  checking: boolean;
  signIn: (email: string) => Promise<AccessState>;
  signUp: (params: RegisterParams) => Promise<AccessState>;
  signOut: () => void;
  refresh: () => Promise<void>;
  setAccess: (state: AccessState) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [access, setAccess] = useState<AccessState | null>(null);
  const [checking, setChecking] = useState(true);

  // Код лежит в localStorage: после перезагрузки проверяем, что он ещё жив.
  useEffect(() => {
    if (!getStoredEmail()) {
      setChecking(false);
      return;
    }

    let cancelled = false;
    fetchAccessState()
      .then((state) => !cancelled && setAccess(state))
      .catch(() => {
        if (!cancelled) storeEmail(null);
      })
      .finally(() => !cancelled && setChecking(false));

    return () => {
      cancelled = true;
    };
  }, []);

  const signIn = useCallback(async (email: string) => {
    // Почту сохраняем до запроса: заголовок X-Access-Email берётся из localStorage.
    const previous = getStoredEmail();
    storeEmail(email);
    try {
      const state = await loginRequest(email);
      setAccess(state);
      return state;
    } catch (error) {
      storeEmail(previous);
      throw error;
    }
  }, []);

  const signUp = useCallback(async (params: RegisterParams) => {
    // Регистрация сама заводит учётку, поэтому почту кладём заранее — по ней пойдут
    // следующие запросы. Не удалось — возвращаем прежнюю.
    const previous = getStoredEmail();
    storeEmail(params.email);
    try {
      const state = await registerRequest(params);
      setAccess(state);
      return state;
    } catch (error) {
      storeEmail(previous);
      throw error;
    }
  }, []);

  const signOut = useCallback(() => {
    storeEmail(null);
    setAccess(null);
  }, []);

  const refresh = useCallback(async () => {
    try {
      setAccess(await fetchAccessState());
    } catch (error) {
      // Код отозвали или он исчерпан — возвращаем гостя на экран входа.
      if (error instanceof ApiError && error.status === 401) {
        storeEmail(null);
        setAccess(null);
      }
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ access, checking, signIn, signUp, signOut, refresh, setAccess }),
    [access, checking, signIn, signUp, signOut, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth вызван вне AuthProvider");
  return value;
}

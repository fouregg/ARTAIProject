import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import {
  ApiError,
  fetchAccessState,
  getStoredCode,
  login as loginRequest,
  register as registerRequest,
  storeCode,
} from "../api/client";
import type { AccessState, RegisterParams } from "../api/client";

interface AuthContextValue {
  access: AccessState | null;
  checking: boolean;
  signIn: (code: string) => Promise<AccessState>;
  signUp: (code: string, params: RegisterParams) => Promise<AccessState>;
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
    if (!getStoredCode()) {
      setChecking(false);
      return;
    }

    let cancelled = false;
    fetchAccessState()
      .then((state) => !cancelled && setAccess(state))
      .catch(() => {
        if (!cancelled) storeCode(null);
      })
      .finally(() => !cancelled && setChecking(false));

    return () => {
      cancelled = true;
    };
  }, []);

  const signIn = useCallback(async (code: string) => {
    // Код сохраняем до запроса: заголовок X-Access-Code берётся из localStorage.
    const previous = getStoredCode();
    storeCode(code);
    try {
      const state = await loginRequest(code);
      setAccess(state);
      return state;
    } catch (error) {
      storeCode(previous);
      throw error;
    }
  }, []);

  const signUp = useCallback(async (code: string, params: RegisterParams) => {
    const previous = getStoredCode();
    storeCode(code);
    try {
      const state = await registerRequest(params);
      setAccess(state);
      return state;
    } catch (error) {
      storeCode(previous);
      throw error;
    }
  }, []);

  const signOut = useCallback(() => {
    storeCode(null);
    setAccess(null);
  }, []);

  const refresh = useCallback(async () => {
    try {
      setAccess(await fetchAccessState());
    } catch (error) {
      // Код отозвали или он исчерпан — возвращаем гостя на экран входа.
      if (error instanceof ApiError && error.status === 401) {
        storeCode(null);
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

export type LanguageChoice = "auto" | "ru" | "en" | "zh" | "fr" | "es" | "pt" | "ar";
export type AspectRatio = "1:1" | "3:2" | "2:3";
export type Quality = "auto" | "low" | "medium" | "high";
export type JobStage = "queued" | "translating" | "generating" | "done" | "error";

export interface Generation {
  id: string;
  url: string;
  /** Лёгкое превью: коллаж и галерея берут его вместо оригинала. */
  thumb_url: string;
  prompt_original: string;
  prompt_translated: string | null;
  source_lang: string | null;
  detected_lang: string | null;
  translation_degraded: boolean;
  size: string;
  quality: string;
  created_at: string;
  /** Когда файл удалят, если не сохранить в галерею и не отправить на купол. */
  expires_at: string;
}

export interface JobStatus {
  job_id: string;
  status: "pending" | "running" | "done" | "error";
  stage: JobStage;
  generation: Generation | null;
  error: string | null;
  error_code: string | null;
}

export interface GenerateParams {
  prompt: string;
  lang: LanguageChoice;
  aspect_ratio: AspectRatio;
  quality: Quality;
  skip_translation?: boolean;
  original_prompt?: string;
}

export interface GalleryItem {
  id: number;
  generation_id: string;
  url: string;
  /** Лёгкое превью: коллаж и галерея берут его вместо оригинала. */
  thumb_url: string;
  title: string | null;
  prompt_original: string;
  prompt_translated: string | null;
  detected_lang: string | null;
  created_at: string;
}

export interface DomeItem {
  id: number;
  generation_id: string;
  url: string;
  /** Лёгкое превью: коллаж и галерея берут его вместо оригинала. */
  thumb_url: string;
  prompt: string;
  position: number;
  created_at: string;
}

export interface AccessState {
  code: string;
  limit: number;
  used: number;
  remaining: number;
  /** Анкета участника заполнена и обе отметки проставлены. */
  registered: boolean;
}

export interface LegalDocument {
  key: "agreement" | "consent";
  title: string;
  version: string;
  sha256: string;
  text: string;
}

export interface LegalBundle {
  documents: LegalDocument[];
  policy_url: string;
  checkbox_agreement: string;
  checkbox_consent: string;
  age_notice: string;
  ai_disclosure: string;
  rejection_notice: string;
}

export interface RegisterParams {
  last_name: string;
  first_name: string;
  middle_name: string | null;
  birth_date: string;
  country: string;
  is_legal_representative: boolean;
  accepted: { key: string; version: string; sha256: string }[];
  ui_language: string;
}

const CODE_STORAGE_KEY = "artai.code";

export function getStoredCode(): string | null {
  return localStorage.getItem(CODE_STORAGE_KEY);
}

export function storeCode(code: string | null): void {
  if (code) localStorage.setItem(CODE_STORAGE_KEY, code);
  else localStorage.removeItem(CODE_STORAGE_KEY);
}

export interface AdminDomeItem {
  id: number;
  generation_id: string;
  url: string;
  /** Лёгкое превью: коллаж и галерея берут его вместо оригинала. */
  thumb_url: string;
  prompt_original: string;
  prompt_translated: string | null;
  detected_lang: string | null;
  is_visible: boolean;
  position: number;
  created_at: string;
}

export class ApiError extends Error {
  constructor(message: string, readonly status: number, readonly code?: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const code = getStoredCode();
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      // Код доступа — он же учётка: одного заголовка достаточно, сессий не заводим.
      ...(code ? { "X-Access-Code": code } : {}),
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      message = body.detail ?? body.message ?? message;
    } catch {
      /* тело не JSON — оставляем код статуса */
    }
    throw new ApiError(message, response.status);
  }

  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}

export function login(code: string): Promise<AccessState> {
  return request("/api/auth/login", { method: "POST", body: JSON.stringify({ code }) });
}

export function fetchAccessState(): Promise<AccessState> {
  return request("/api/auth/me");
}

export function fetchLegal(): Promise<LegalBundle> {
  return request("/api/legal");
}

export function register(params: RegisterParams): Promise<AccessState> {
  return request("/api/auth/register", { method: "POST", body: JSON.stringify(params) });
}

export function startGeneration(params: GenerateParams): Promise<{ job_id: string }> {
  return request("/api/generate", { method: "POST", body: JSON.stringify(params) });
}

export function getJob(jobId: string): Promise<JobStatus> {
  return request(`/api/jobs/${jobId}`);
}

const POLL_INTERVAL_MS = 1000;
const POLL_TIMEOUT_MS = 5 * 60 * 1000;

/** Опрашивает задачу до готовности; onStage показывает пользователю текущий шаг. */
export async function waitForGeneration(
  jobId: string,
  onStage: (stage: JobStage) => void,
  signal?: AbortSignal,
): Promise<Generation> {
  const deadline = Date.now() + POLL_TIMEOUT_MS;

  while (Date.now() < deadline) {
    if (signal?.aborted) throw new DOMException("aborted", "AbortError");

    const job = await getJob(jobId);
    onStage(job.stage);

    if (job.status === "done" && job.generation) return job.generation;
    if (job.status === "error") {
      throw new ApiError(job.error ?? "Ошибка генерации", 500, job.error_code ?? undefined);
    }

    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
  }

  throw new ApiError("Генерация не завершилась вовремя.", 504, "TIMEOUT");
}

export function saveToGallery(generationId: string): Promise<GalleryItem> {
  return request("/api/gallery", {
    method: "POST",
    body: JSON.stringify({ generation_id: generationId }),
  });
}

export function fetchGallery(): Promise<GalleryItem[]> {
  return request("/api/gallery");
}

export function deleteGalleryItem(id: number): Promise<void> {
  return request(`/api/gallery/${id}`, { method: "DELETE" });
}

export function displayOnDome(generationId: string): Promise<DomeItem> {
  return request("/api/dome/display", {
    method: "POST",
    body: JSON.stringify({ generation_id: generationId }),
  });
}

export function fetchDomeItems(token: string): Promise<DomeItem[]> {
  return request(`/api/dome/items?token=${encodeURIComponent(token)}`);
}

// --- модерация холста: собственный токен, отдельный от токена экрана ---

export function fetchAdminDome(token: string): Promise<AdminDomeItem[]> {
  return request(`/api/admin/dome?token=${encodeURIComponent(token)}`);
}

export function hideDomeItem(token: string, id: number): Promise<AdminDomeItem> {
  return request(`/api/admin/dome/${id}?token=${encodeURIComponent(token)}`, { method: "DELETE" });
}

export function restoreDomeItem(token: string, id: number): Promise<AdminDomeItem> {
  return request(`/api/admin/dome/${id}/restore?token=${encodeURIComponent(token)}`, {
    method: "POST",
  });
}

export function clearDome(token: string): Promise<void> {
  return request(`/api/admin/dome?token=${encodeURIComponent(token)}`, { method: "DELETE" });
}

/** ws:// или wss:// подбирается от текущей страницы — работает и в LAN, и через туннель. */
export function domeSocketUrl(token: string): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/dome?token=${encodeURIComponent(token)}`;
}

const STORAGE_KEY = "webrate:lastSubmittedUrl";
export const WEBSITE_URL_COOKIE = "webrate_url";

/**
 * Persists the submitted URL client-side so it survives navigation from
 * the landing page through scanning to the dashboard: sessionStorage for
 * same-tab convenience, and a cookie so dashboard Server Components (which
 * can't read sessionStorage) can read it too via next/headers `cookies()`.
 */
export function storeSubmittedUrl(url: string) {
  try {
    sessionStorage.setItem(STORAGE_KEY, url);
  } catch {
    // sessionStorage unavailable (e.g. private browsing) — safe to ignore.
  }
  try {
    document.cookie = `${WEBSITE_URL_COOKIE}=${encodeURIComponent(url)}; path=/; max-age=86400; samesite=lax`;
  } catch {
    // document unavailable — safe to ignore.
  }
}

export function readSubmittedUrl(): string | null {
  try {
    return sessionStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

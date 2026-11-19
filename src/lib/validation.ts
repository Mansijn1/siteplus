export type UrlValidationResult =
  | { ok: true; normalizedUrl: string }
  | { ok: false; error: string };

/**
 * Validates and normalizes a user-entered website URL.
 * - Rejects empty input.
 * - Adds https:// when no protocol is given.
 * - Only accepts http/https protocols.
 * - Requires a plausible hostname (contains a dot, no spaces).
 */
export function validateAndNormalizeUrl(input: string): UrlValidationResult {
  const trimmed = input.trim();

  if (!trimmed) {
    return { ok: false, error: "Please enter a website URL." };
  }

  if (/\s/.test(trimmed)) {
    return { ok: false, error: "URLs can't contain spaces. Check for typos and try again." };
  }

  const candidate = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;

  let parsed: URL;
  try {
    parsed = new URL(candidate);
  } catch {
    return {
      ok: false,
      error: "That doesn't look like a valid URL. Try something like yourwebsite.com",
    };
  }

  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    return { ok: false, error: "Only http and https websites are supported." };
  }

  if (!parsed.hostname.includes(".") || parsed.hostname.startsWith(".") || parsed.hostname.endsWith(".")) {
    return { ok: false, error: "Please enter a valid domain, e.g. yourwebsite.com" };
  }

  parsed.hostname = parsed.hostname.toLowerCase();

  return { ok: true, normalizedUrl: parsed.toString() };
}

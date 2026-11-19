export const HERO_URL_INPUT_ID = "hero-url-input";

/** Scrolls to the hero URL input and focuses it. Used by nav and final CTA. */
export function scrollToHeroInput() {
  const el = document.getElementById(HERO_URL_INPUT_ID);
  if (!el) return;
  el.scrollIntoView({ behavior: "smooth", block: "center" });
  window.setTimeout(() => (el as HTMLInputElement).focus(), 400);
}

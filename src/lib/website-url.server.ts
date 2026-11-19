import "server-only";
import { cookies } from "next/headers";
import { DEMO_WEBSITE_URL } from "@/data/demo-results";
import { WEBSITE_URL_COOKIE } from "./site-url-storage";

/**
 * Reads the website URL the visitor actually submitted (persisted as a
 * cookie when they left the landing page), falling back to the canonical
 * demo URL for anyone who lands on the dashboard directly. Server-only —
 * never import this from a Client Component.
 */
export async function getWebsiteUrl(): Promise<string> {
  const store = await cookies();
  const raw = store.get(WEBSITE_URL_COOKIE)?.value;
  return raw ? decodeURIComponent(raw) : DEMO_WEBSITE_URL;
}

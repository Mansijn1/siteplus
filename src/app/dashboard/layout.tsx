import type { Metadata } from "next";
import { DashboardShell } from "@/components/dashboard/dashboard-shell";
import { getWebsiteUrl } from "@/lib/website-url.server";

export const metadata: Metadata = {
  title: "Dashboard — WebRate AI",
  description: "Demo evaluation dashboard for WebRate AI.",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  // Intentionally not awaited here — passed down as a promise so only the
  // small client-side URL display suspends, not the whole shell.
  const websiteUrlPromise = getWebsiteUrl();
  return <DashboardShell websiteUrlPromise={websiteUrlPromise}>{children}</DashboardShell>;
}

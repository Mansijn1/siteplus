import { Suspense } from "react";
import { getWebsiteUrl } from "@/lib/website-url.server";
import { OverviewDashboard } from "@/components/dashboard/overview-dashboard";

export default function DashboardOverviewPage() {
  return (
    <Suspense fallback={<div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:py-10" />}>
      <OverviewContent />
    </Suspense>
  );
}

async function OverviewContent() {
  const websiteUrl = await getWebsiteUrl();
  return <OverviewDashboard websiteUrl={websiteUrl} />;
}

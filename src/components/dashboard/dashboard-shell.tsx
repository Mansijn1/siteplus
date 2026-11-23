"use client";

import { Suspense, use, useState } from "react";
import Link from "next/link";
import { Menu, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Wordmark } from "@/components/shared/brand-mark";
import { SidebarNav } from "./sidebar-nav";
import { AUDIT_STATUS, DEMO_WEBSITE_URL } from "@/data/demo-results";
import { EvaluationDataProvider, useEvaluationData } from "./evaluation-data-provider";

function toDisplayUrl(url: string) {
  return url.replace(/^https?:\/\//, "");
}

function ResolvedUrlText({ websiteUrlPromise }: { websiteUrlPromise: Promise<string> }) {
  const url = use(websiteUrlPromise);
  return <span className="truncate font-mono text-sm text-foreground/85">{toDisplayUrl(url)}</span>;
}

export function DashboardShell({
  children,
  websiteUrlPromise,
}: {
  children: React.ReactNode;
  websiteUrlPromise: Promise<string>;
}) {
  return (
    <EvaluationDataProvider>
      <ShellBody websiteUrlPromise={websiteUrlPromise}>{children}</ShellBody>
    </EvaluationDataProvider>
  );
}

function ShellBody({
  children,
  websiteUrlPromise,
}: {
  children: React.ReactNode;
  websiteUrlPromise: Promise<string>;
}) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const { phase } = useEvaluationData();
  const modeLabel = phase === "real" ? "Live Evaluation" : phase === "loading" ? "Evaluating…" : "Demo Audit";

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="no-print hidden w-64 shrink-0 border-r border-border bg-secondary/30 lg:flex lg:flex-col">
        <div className="flex h-16 items-center px-5">
          <Link href="/">
            <Wordmark />
          </Link>
        </div>
        <div className="flex-1 py-2">
          <SidebarNav />
        </div>
        <div className="border-t border-border p-4">
          <p className="font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">
            {phase === "real" ? "Live Evaluation Dashboard" : "Demo Audit Dashboard"}
          </p>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="no-print sticky top-0 z-40 flex h-16 items-center gap-4 border-b border-border bg-background/95 px-4 backdrop-blur-sm sm:px-6">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            aria-label="Open navigation"
            onClick={() => setMobileNavOpen(true)}
          >
            <Menu className="size-5" />
          </Button>

          <div className="flex min-w-0 flex-1 items-center gap-2.5">
            <Globe className="size-4 shrink-0 text-muted-foreground" />
            <Suspense
              fallback={
                <span className="truncate font-mono text-sm text-foreground/85">
                  {toDisplayUrl(DEMO_WEBSITE_URL)}
                </span>
              }
            >
              <ResolvedUrlText websiteUrlPromise={websiteUrlPromise} />
            </Suspense>
            <span className="shrink-0 rounded-sm bg-pass/10 px-2 py-0.5 font-mono text-[10px] font-medium uppercase tracking-[0.08em] text-pass">
              {AUDIT_STATUS}
            </span>
            <span className="hidden shrink-0 rounded-sm bg-secondary px-2 py-0.5 font-mono text-[10px] font-medium uppercase tracking-[0.08em] text-muted-foreground sm:inline-block">
              {modeLabel}
            </span>
          </div>

          <Button
            variant="outline"
            size="sm"
            nativeButton={false}
            className="hidden sm:inline-flex"
            render={<Link href="/" />}
          >
            Back to Site
          </Button>
        </header>

        <main className="flex-1 bg-background">{children}</main>
      </div>

      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent side="left" className="w-[280px] p-0">
          <SheetHeader className="h-16 justify-center border-b border-border px-5">
            <SheetTitle>
              <Wordmark />
            </SheetTitle>
          </SheetHeader>
          <div className="py-2">
            <SidebarNav onNavigate={() => setMobileNavOpen(false)} />
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}

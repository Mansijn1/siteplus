"use client";

import { useEffect, useState } from "react";
import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetClose,
} from "@/components/ui/sheet";
import { Wordmark } from "@/components/shared/brand-mark";
import { scrollToHeroInput } from "@/lib/scroll-to-hero";

const NAV_LINKS = [
  { href: "#product", label: "Product" },
  { href: "#features", label: "Features" },
  { href: "#how-it-works", label: "How It Works" },
  { href: "#evaluation", label: "Evaluation" },
];

export function SiteHeader() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`sticky top-0 z-50 w-full border-b transition-colors ${
        scrolled ? "border-border bg-background/92 backdrop-blur-sm" : "border-transparent bg-background"
      }`}
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <a href="#top" className="text-[17px]">
          <Wordmark />
        </a>

        <nav className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <Button variant="ghost" size="sm" className="text-sm">
            Sign In
          </Button>
          <Button size="sm" className="text-sm" onClick={scrollToHeroInput}>
            Get Started
          </Button>
        </div>

        <Sheet>
          <SheetTrigger
            render={<Button variant="ghost" size="icon" className="md:hidden" aria-label="Open menu" />}
          >
            <Menu className="size-5" />
          </SheetTrigger>
          <SheetContent side="right" className="w-[280px]">
            <SheetHeader>
              <SheetTitle>
                <Wordmark />
              </SheetTitle>
            </SheetHeader>
            <nav className="mt-4 flex flex-col gap-1 px-4">
              {NAV_LINKS.map((link) => (
                <SheetClose
                  key={link.href}
                  render={
                    <a
                      href={link.href}
                      className="rounded-md px-2 py-2.5 text-sm text-foreground/90 hover:bg-secondary"
                    />
                  }
                >
                  {link.label}
                </SheetClose>
              ))}
            </nav>
            <div className="mt-4 flex flex-col gap-2 px-4">
              <Button variant="outline">Sign In</Button>
              <SheetClose render={<Button onClick={scrollToHeroInput} />}>Get Started</SheetClose>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </header>
  );
}

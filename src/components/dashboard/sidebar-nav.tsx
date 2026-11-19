"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ClipboardList,
  LayoutGrid,
  Lightbulb,
  FileBarChart,
  Settings,
  type LucideIcon,
} from "lucide-react";

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  /** Items without a built-out page render a polished placeholder instead. */
  placeholder?: boolean;
}

export const DASHBOARD_NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/evaluation", label: "Website Evaluation", icon: ClipboardList },
  { href: "/dashboard/categories", label: "Category Analysis", icon: LayoutGrid },
  { href: "/dashboard/recommendations", label: "Recommendations", icon: Lightbulb },
  { href: "/dashboard/reports", label: "Reports", icon: FileBarChart, placeholder: true },
  { href: "/dashboard/settings", label: "Settings", icon: Settings, placeholder: true },
];

function isActive(pathname: string, href: string) {
  if (href === "/dashboard") return pathname === "/dashboard";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="flex flex-col gap-0.5 px-3">
      {DASHBOARD_NAV_ITEMS.map((item) => {
        const active = isActive(pathname, item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
              active
                ? "bg-secondary font-medium text-flag"
                : "text-foreground/75 hover:bg-secondary/60 hover:text-foreground"
            }`}
          >
            <item.icon className="size-[18px] shrink-0" strokeWidth={1.75} />
            <span className="truncate">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

interface NavItem {
  href: string;
  label: string;
  matches: string[];
  adminOnly?: boolean;
}

const navigationItems: NavItem[] = [
  { href: "/", label: "Dashboard", matches: ["/"] },
  { href: "/ask", label: "Shipments", matches: ["/ask"] },
  { href: "/thread", label: "Follow-up Thread", matches: ["/thread"] },
  {
    href: "/result",
    label: "Compliance Result",
    matches: ["/result", "/result-error", "/result-insufficient"],
  },
  { href: "/history", label: "Shipment History", matches: ["/history"] },
  { href: "/library", label: "Regulations Library", matches: ["/library"] },
  { href: "/agreements", label: "Carrier Agreements", matches: ["/agreements"] },
  { href: "/admin/review", label: "Audit Review", matches: ["/admin/review"], adminOnly: true },
  { href: "/admin/upload", label: "Document Ingestion", matches: ["/admin/upload"], adminOnly: true },
];

export default function Navigation() {
  const pathname = usePathname();
  const { isAdmin } = useAuth();

  return (
    <nav className="nav-links" aria-label="Primary navigation">
      {navigationItems.map((item) => {
        // Hide admin-only links for non-admins to keep navigation clean
        if (item.adminOnly && !isAdmin) {
          return null;
        }

        const isActive = item.matches.includes(pathname);

        return (
          <Link
            key={item.href}
            href={item.href}
            className={`nav-link${isActive ? " active" : ""} flex items-center justify-between`}
            aria-current={isActive ? "page" : undefined}
          >
            <span>{item.label}</span>
            {item.adminOnly && (
              <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                Admin
              </span>
            )}
          </Link>
        );
      })}
    </nav>
  );
}


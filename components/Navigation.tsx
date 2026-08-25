"use client";

import { usePathname } from "next/navigation";

const navigationItems = [
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
  { href: "/admin/review", label: "Audit Review", matches: ["/admin/review"] },
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="nav-links" aria-label="Primary navigation">
      {navigationItems.map((item) => {
        const isActive = item.matches.includes(pathname);

        return (
          <a
            key={item.href}
            href={item.href}
            className={`nav-link${isActive ? " active" : ""}`}
            aria-current={isActive ? "page" : undefined}
          >
            {item.label}
          </a>
        );
      })}
    </nav>
  );
}

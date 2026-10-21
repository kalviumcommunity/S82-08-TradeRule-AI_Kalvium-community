import "./globals.css";
import type { Metadata } from "next";
import Navigation from "@/components/Navigation";
import HeaderUserNav from "@/components/HeaderUserNav";
import { AuthProvider } from "@/context/AuthContext";

export const metadata: Metadata = {
  title: "TradeRule AI",
  description: "Compliance Q&A tool for shipping and logistics operations coordinators",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {/* Top bar matching the dark logistics dashboard theme */}
          <header className="dashboard-nav">
            <div className="flex items-center gap-3">
              <div className="brand-mark">
                TR
              </div>
              <span className="font-bold tracking-tight text-white uppercase text-sm">TradeRule AI</span>
            </div>
            
            <HeaderUserNav />
          </header>

          <div className="app-shell">
            <aside className="sidebar">
              <Navigation />
            </aside>

            <div className="app-content">
              {/* Main Content */}
              <main className="max-w-[960px] mx-auto px-10 pt-8 pb-20">{children}</main>

              {/* Footer */}
              <footer className="py-6 px-10 text-slate-500 text-xs text-center border-t border-slate-200">
                &copy; {new Date().getFullYear()} TradeRule AI Operations. All rights reserved.
              </footer>
            </div>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
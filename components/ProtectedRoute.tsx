"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
}

export default function ProtectedRoute({
  children,
  requireAdmin = false,
}: ProtectedRouteProps) {
  const { user, loading, isAdmin } = useAuth();
  const pathname = usePathname();

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-3">
        <div className="w-8 h-8 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm text-slate-400">Verifying session credentials...</p>
      </div>
    );
  }

  // Not authenticated
  if (!user) {
    const returnUrl = encodeURIComponent(pathname);
    return (
      <div className="max-w-md mx-auto my-12 p-8 bg-slate-900 border border-slate-800 rounded-xl text-center shadow-xl">
        <div className="w-12 h-12 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
          TR
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Authentication Required</h2>
        <p className="text-sm text-slate-400 mb-6">
          You must be signed in to access this TradeRule AI compliance workspace.
        </p>
        <div className="flex flex-col gap-3">
          <Link
            href={`/login?returnTo=${returnUrl}`}
            className="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg text-sm transition-colors text-center"
          >
            Sign In to Continue
          </Link>
          <Link
            href={`/register?returnTo=${returnUrl}`}
            className="w-full py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium rounded-lg text-sm transition-colors text-center"
          >
            Create New Account
          </Link>
        </div>
      </div>
    );
  }

  // Authenticated but lacks required admin role
  if (requireAdmin && !isAdmin) {
    return (
      <div className="max-w-lg mx-auto my-12 p-8 bg-slate-900 border border-amber-500/30 rounded-xl text-center shadow-xl">
        <div className="w-12 h-12 bg-amber-500/10 text-amber-400 rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
          !
        </div>
        <div className="inline-block px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 text-xs font-semibold uppercase tracking-wider mb-3">
          403 Forbidden
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Administrator Access Required</h2>
        <p className="text-sm text-slate-400 mb-6">
          Your account (<span className="text-slate-200">{user.email}</span>) holds the standard{" "}
          <strong className="text-slate-200">user</strong> role. Administrative privileges are required to view audit logs or manage compliance knowledge documents.
        </p>
        <Link
          href="/"
          className="inline-block py-2.5 px-5 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-lg text-sm transition-colors"
        >
          Return to Operations Dashboard
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}

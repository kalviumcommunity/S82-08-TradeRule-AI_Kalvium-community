"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function HeaderUserNav() {
  const { user, logout, loading, isAdmin } = useAuth();
  const router = useRouter();

  if (loading) {
    return (
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-full bg-slate-800 animate-pulse"></div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex items-center gap-3">
        <Link
          href="/login"
          className="px-3.5 py-1.5 text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors border border-slate-700"
        >
          Sign In
        </Link>
        <Link
          href="/register"
          className="px-3.5 py-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 rounded-lg transition-colors shadow-sm"
        >
          Register
        </Link>
      </div>
    );
  }

  const initials =
    user.full_name
      ?.split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2) ||
    user.email.slice(0, 2).toUpperCase();

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <div className="flex items-center gap-4">
      <div className="user-profile">
        <div className="user-avatar bg-emerald-700 text-white font-bold">{initials}</div>
        <div className="text-left leading-tight hidden sm:block">
          <div className="font-semibold text-white text-sm flex items-center gap-1.5">
            <span>{user.full_name || user.email.split("@")[0]}</span>
            {isAdmin && (
              <span className="px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 text-[10px] font-bold uppercase tracking-wider border border-amber-500/30">
                Admin
              </span>
            )}
          </div>
          <div className="text-xs text-slate-400 capitalize">
            {isAdmin ? "Compliance Administrator" : "Logistics Operator"}
          </div>
        </div>
      </div>

      <button
        type="button"
        onClick={handleLogout}
        className="px-2.5 py-1.5 text-xs font-medium text-slate-400 hover:text-rose-300 hover:bg-rose-500/10 rounded-md transition-colors cursor-pointer border border-transparent hover:border-rose-500/20"
        title="Sign Out"
      >
        Sign Out
      </button>
    </div>
  );
}

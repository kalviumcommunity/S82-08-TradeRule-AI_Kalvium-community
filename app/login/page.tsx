"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnTo = searchParams.get("returnTo") || "/";

  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const result = await login(email, password);
    setLoading(false);

    if (result.success) {
      router.push(returnTo);
    } else {
      setError(result.error || "Authentication failed.");
    }
  };

  const setDemoCredentials = (role: "admin" | "user") => {
    if (role === "admin") {
      setEmail("admin@traderule.ai");
      setPassword("admin123");
    } else {
      setEmail("user1@example.com");
      setPassword("user@123");
    }
  };

  return (
    <div className="max-w-md mx-auto my-10">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 font-bold text-lg mb-3 border border-emerald-500/20">
            TR
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Sign In</h1>
          <p className="text-sm text-slate-400 mt-1">
            Access TradeRule AI Compliance Workspace
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-start gap-3">
            <span className="font-bold">!</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="operator@company.com"
              className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold rounded-lg text-sm transition-colors shadow-lg shadow-emerald-900/30 flex items-center justify-center gap-2 mt-6 cursor-pointer"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Signing in...</span>
              </>
            ) : (
              <span>Sign In</span>
            )}
          </button>
        </form>

        {/* Demo Accounts Quick-Fill */}
        <div className="mt-8 pt-6 border-t border-slate-800">
          <p className="text-xs text-slate-400 font-medium mb-3 text-center">
            Quick fill test accounts:
          </p>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setDemoCredentials("admin")}
              className="py-1.5 px-3 bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 text-xs text-slate-300 rounded-md transition-colors text-center"
            >
              Fill Admin
            </button>
            <button
              type="button"
              onClick={() => setDemoCredentials("user")}
              className="py-1.5 px-3 bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 text-xs text-slate-300 rounded-md transition-colors text-center"
            >
              Fill User
            </button>
          </div>
        </div>

        <div className="mt-6 text-center text-xs text-slate-400">
          Do not have an account?{" "}
          <Link
            href={`/register?returnTo=${encodeURIComponent(returnTo)}`}
            className="text-emerald-400 hover:text-emerald-300 font-medium underline underline-offset-4"
          >
            Register here
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="text-center py-20 text-slate-400">Loading sign in...</div>}>
      <LoginForm />
    </Suspense>
  );
}

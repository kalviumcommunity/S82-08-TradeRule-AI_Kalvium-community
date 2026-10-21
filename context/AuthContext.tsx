"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "user" | "admin" | string;
  created_at?: string | null;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (
    email: string,
    password: string,
    fullName?: string
  ) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE_URL =
  process.env.NEXT_PUBLIC_RAG_API_URL || "http://127.0.0.1:8000";

const TOKEN_KEY = "traderule_auth_token";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Restore session from token / cookies on initial load
  const restoreSession = useCallback(async (existingToken?: string | null) => {
    try {
      const activeToken = existingToken || (typeof window !== "undefined" ? sessionStorage.getItem(TOKEN_KEY) : null);
      const headers: Record<string, string> = {};
      if (activeToken) {
        headers["Authorization"] = `Bearer ${activeToken}`;
      }

      const res = await fetch(`${API_BASE_URL}/auth/me`, {
        method: "GET",
        headers,
        credentials: "include",
      });

      if (res.ok) {
        const userData: User = await res.json();
        setUser(userData);
        if (activeToken) {
          setToken(activeToken);
        }
      } else {
        setUser(null);
        setToken(null);
        if (typeof window !== "undefined") {
          sessionStorage.removeItem(TOKEN_KEY);
        }
      }
    } catch {
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  const login = async (email: string, password: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        return {
          success: false,
          error: errorData.detail || "Invalid email or password.",
        };
      }

      const data = await res.json();
      setUser(data.user);
      setToken(data.token);
      if (typeof window !== "undefined") {
        sessionStorage.setItem(TOKEN_KEY, data.token);
      }
      return { success: true };
    } catch (err: unknown) {
      return {
        success: false,
        error: err instanceof Error ? err.message : "Network error. Please try again.",
      };
    }
  };

  const register = async (email: string, password: string, fullName = "") => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        return {
          success: false,
          error: errorData.detail || "Registration failed. Please check your details.",
        };
      }

      const data = await res.json();
      setUser(data.user);
      setToken(data.token);
      if (typeof window !== "undefined") {
        sessionStorage.setItem(TOKEN_KEY, data.token);
      }
      return { success: true };
    } catch (err: unknown) {
      return {
        success: false,
        error: err instanceof Error ? err.message : "Network error. Please try again.",
      };
    }
  };

  const logout = async () => {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch {
      // Ignore network errors on logout
    } finally {
      setUser(null);
      setToken(null);
      if (typeof window !== "undefined") {
        sessionStorage.removeItem(TOKEN_KEY);
      }
    }
  };

  const isAdmin = user?.role === "admin";

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        isAdmin,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

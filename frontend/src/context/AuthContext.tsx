"use client";

import axios from "axios";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

type AuthContextType = {
  token: string | null;
  displayName: string | null;
  isAuthenticated: boolean;
  login: (token: string, name?: string) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const storedName = typeof window !== "undefined" ? localStorage.getItem("userName") : null;
    if (storedToken) {
      setToken(storedToken);
      axios.defaults.headers.common["Authorization"] = `Bearer ${storedToken}`;
    }
    if (storedName) {
      setDisplayName(storedName);
    }
  }, []);

  const login = useCallback((newToken: string, name?: string) => {
    setToken(newToken);
    axios.defaults.headers.common["Authorization"] = `Bearer ${newToken}`;
    localStorage.setItem("token", newToken);
    if (name) {
      setDisplayName(name);
      localStorage.setItem("userName", name);
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setDisplayName(null);
    axios.defaults.headers.common["Authorization"] = "";
    localStorage.removeItem("token");
    localStorage.removeItem("userName");
  }, []);

  const value = useMemo(
    () => ({
      token,
      displayName,
      isAuthenticated: Boolean(token),
      login,
      logout,
    }),
    [token, displayName, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};


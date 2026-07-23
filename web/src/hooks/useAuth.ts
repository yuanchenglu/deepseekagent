import { createContext, useContext, useEffect, useState } from "react";
import { api, setAuthToken, getAuthToken } from "@/lib/api";

interface AuthState {
  loading: boolean;
  authenticated: boolean;
  username: string | null;
  hasUsers: boolean | null;
  login: (login: string, password: string) => Promise<string | null>;
  register: (username: string, password: string, email?: string, phone?: string) => Promise<string | null>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);
  const [username, setUsername] = useState<string | null>(null);
  const [hasUsers, setHasUsers] = useState<boolean | null>(null);

  const checkAuth = async () => {
    try {
      const me = await api.getMe();
      if (me.authenticated) {
        setAuthenticated(true);
        setUsername(me.username || null);
      } else {
        setAuthenticated(false);
        setUsername(null);
        setAuthToken(null);
      }
    } catch {
      setAuthenticated(false);
      setUsername(null);
    }
  };

  const checkHasUsers = async () => {
    try {
      const resp = await api.hasUsers();
      setHasUsers(resp.has_users);
    } catch {
      setHasUsers(null);
    }
  };

  useEffect(() => {
    const token = getAuthToken();
    if (token) {
      checkAuth().finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
    checkHasUsers();
  }, []);

  const login = async (loginStr: string, password: string): Promise<string | null> => {
    const resp = await api.login(loginStr, password);
    if (resp.ok && resp.token) {
      setAuthToken(resp.token);
      setAuthenticated(true);
      setUsername(resp.username || loginStr);
      return null;
    }
    return resp.message;
  };

  const register = async (username: string, password: string, email?: string, phone?: string): Promise<string | null> => {
    const resp = await api.register(username, password, email, phone);
    if (resp.ok && resp.token) {
      setAuthToken(resp.token);
      setAuthenticated(true);
      setUsername(username);
      setHasUsers(true);
      return null;
    }
    return resp.message;
  };

  const logout = () => {
    setAuthToken(null);
    setAuthenticated(false);
    setUsername(null);
  };

  return (
    <AuthContext.Provider value={{ loading, authenticated, username, hasUsers, login, register, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

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
        setUsername(me.user?.username || null);
      } else {
        setAuthenticated(false);
        setUsername(null);
        setAuthToken(null);
      }
    } catch {
      setAuthenticated(false);
      setUsername(null);
      setAuthToken(null);
    }
  };

  useEffect(() => {
    const token = getAuthToken();
    const init = token ? api.getMe() : Promise.resolve(null);
    init
      .then((me) => {
        if (me && me.authenticated) {
          setAuthenticated(true);
          setUsername(me.user?.username || null);
        } else {
          setAuthenticated(false);
          setUsername(null);
          setAuthToken(null);
        }
      })
      .catch(() => {
        setAuthenticated(false);
        setUsername(null);
        setAuthToken(null);
      })
      .finally(() => setLoading(false));
    api
      .authStatus()
      .then((resp) => setHasUsers(resp.has_users))
      .catch(() => setHasUsers(null));
  }, []);

  const login = async (loginStr: string, password: string): Promise<string | null> => {
    try {
      const resp = await api.login(loginStr, password);
      if (resp.ok && resp.token) {
        setAuthToken(resp.token);
        setAuthenticated(true);
        setUsername(resp.user?.username || loginStr);
        return null;
      }
      return resp.message || "Login failed";
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      const match = msg.match(/^\d+:\s*(.*)/);
      return match ? match[1] : msg;
    }
  };

  const register = async (username: string, password: string, email?: string, phone?: string): Promise<string | null> => {
    try {
      const resp = await api.register(username, password, email, phone);
      if (resp.ok && resp.token) {
        setAuthToken(resp.token);
        setAuthenticated(true);
        setUsername(resp.user?.username || username);
        setHasUsers(true);
        return null;
      }
      return resp.message || "Registration failed";
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      const match = msg.match(/^\d+:\s*(.*)/);
      return match ? match[1] : msg;
    }
  };

  const logout = () => {
    api.logout().catch(() => {});
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

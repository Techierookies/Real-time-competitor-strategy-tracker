import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { api, getToken, setToken } from "../lib/api";

interface User {
  id: string;
  name: string;
  email: string;
  isAdmin: boolean;
}

interface AuthContextType {
  user: User | null;
  isAdmin: boolean;
  login: (email: string, password: string, asAdmin?: boolean) => Promise<boolean>;
  logout: () => void;
  signup: (name: string, email: string, password: string) => Promise<boolean>;
}

const PROFILE_KEY = "tracker.profile";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
};

function toUser(result: { name: string; email: string; role: string }): User {
  return {
    id: result.email,
    name: result.name,
    email: result.email,
    // The role comes from the signed token issued by the server. The client
    // no longer tells the server whether it is an admin.
    isAdmin: result.role === "admin",
  };
}

function loadProfile(): User | null {
  if (!getToken()) return null;
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(loadProfile);

  // On reload, confirm the stored token is still valid; drop it if not.
  useEffect(() => {
    if (!getToken()) return;
    api.me().catch(() => {
      setToken(null);
      localStorage.removeItem(PROFILE_KEY);
      setUser(null);
    });
  }, []);

  const remember = (next: User) => {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(next));
    setUser(next);
  };

  const login = async (email: string, password: string, asAdmin = false): Promise<boolean> => {
    try {
      const result = await api.login(email, password);
      const next = toUser(result);
      // The admin login page only admits admins; the server enforces the
      // same rule on every admin endpoint regardless.
      if (asAdmin && !next.isAdmin) {
        setToken(null);
        return false;
      }
      remember(next);
      return true;
    } catch (err) {
      console.error(err);
      return false;
    }
  };

  const signup = async (name: string, email: string, password: string): Promise<boolean> => {
    try {
      remember(toUser(await api.signup(name, email, password)));
      return true;
    } catch (err) {
      console.error(err);
      return false;
    }
  };

  const logout = () => {
    api.logout();
    localStorage.removeItem(PROFILE_KEY);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isAdmin: user?.isAdmin || false, login, logout, signup }}>
      {children}
    </AuthContext.Provider>
  );
};

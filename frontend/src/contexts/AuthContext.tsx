import { createContext, useContext, useState } from "react";
import type {ReactNode} from 'react'

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
  signup: (name: string, email: string, password: string, role?: string) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);

  const login = async (email: string, password: string, asAdmin = false): Promise<boolean> => {
    try {
      const res = await fetch("http://127.0.0.1:8000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, isAdmin: asAdmin }),
      });

      if (!res.ok) return false;

      const data = await res.json();
      setUser({
        id: data.id.toString(),
        name: data.name,
        email: data.email,
        isAdmin: data.role === "admin",
      });
      return true;
    } catch (err) {
      console.error(err);
      return false;
    }
  };

  const signup = async (name: string, email: string, password: string, role = "user"): Promise<boolean> => {
    try {
      const res = await fetch("http://127.0.0.1:8000/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password, role }),
      });

      if (!res.ok) return false;

      const data = await res.json();
      setUser({
        id: data.id?.toString() || "1",
        name: name,
        email: email,
        isAdmin: role === "admin",
      });
      return true;
    } catch (err) {
      console.error(err);
      return false;
    }
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isAdmin: user?.isAdmin || false, login, logout, signup }}>
      {children}
    </AuthContext.Provider>
  );
};

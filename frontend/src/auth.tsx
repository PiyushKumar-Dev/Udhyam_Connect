import { createContext, useContext, useEffect, useState } from "react";

export interface DemoUser {
  username: string;
  display_name: string;
  role: "viewer" | "analyst" | "admin";
}

export const DEMO_USERS: DemoUser[] = [
  { username: "viewer.demo", display_name: "Viewer Demo", role: "viewer" },
  { username: "analyst.demo", display_name: "Analyst Demo", role: "analyst" },
  { username: "admin.demo", display_name: "Admin Demo", role: "admin" }
];

interface AuthContextValue {
  user: DemoUser;
  setUser: (user: DemoUser) => void;
}

const defaultUser = DEMO_USERS[1];
const AuthContext = createContext<AuthContextValue | null>(null);

export function getStoredDemoUser() {
  const saved = window.localStorage.getItem("ubid.demo-user");
  return DEMO_USERS.find((user) => user.username === saved) ?? defaultUser;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUserState] = useState<DemoUser>(defaultUser);

  useEffect(() => {
    setUserState(getStoredDemoUser());
  }, []);

  function setUser(userValue: DemoUser) {
    window.localStorage.setItem("ubid.demo-user", userValue.username);
    setUserState(userValue);
  }

  return <AuthContext.Provider value={{ user, setUser }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return value;
}

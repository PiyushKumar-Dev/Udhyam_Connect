import { ShieldCheck } from "lucide-react";

import { DEMO_USERS, useAuth } from "../auth";

export function AuthSwitcher() {
  const { user, setUser } = useAuth();

  return (
    <div className="flex items-center gap-3 rounded-full border border-border bg-white px-4 py-2 shadow-panel">
      <ShieldCheck className="h-4 w-4 text-primary" />
      <div className="hidden text-left sm:block">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted">Role</p>
        <p className="text-sm font-semibold text-slate-900">{user.display_name}</p>
      </div>
      <select
        className="rounded-full border border-border bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-700 outline-none"
        onChange={(event) => {
          const nextUser = DEMO_USERS.find((item) => item.username === event.target.value);
          if (nextUser) {
            setUser(nextUser);
          }
        }}
        value={user.username}
      >
        {DEMO_USERS.map((item) => (
          <option key={item.username} value={item.username}>
            {item.display_name} ({item.role})
          </option>
        ))}
      </select>
    </div>
  );
}

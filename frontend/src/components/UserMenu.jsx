import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { LogOut, User as UserIcon } from "lucide-react";
import { useLogout, useMe } from "../hooks/useAuth";

function initials(name, email) {
  const source = name?.trim() || email || "";
  if (!source) return "?";
  const parts = source.split(" ").filter(Boolean);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return source.slice(0, 2).toUpperCase();
}

export default function UserMenu() {
  const { data: user } = useMe();
  const logoutMutation = useLogout();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!user) return null;

  function handleLogout() {
    logoutMutation.mutate(undefined, {
      onSettled: () => navigate("/login", { replace: true }),
    });
  }

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex h-8 w-8 items-center justify-center rounded-full bg-teal-700 text-xs font-medium text-white"
        title={user.full_name || user.email}
      >
        {initials(user.full_name, user.email)}
      </button>

      {open && (
        <div className="absolute right-0 top-10 z-10 w-56 rounded-lg border border-stone-200 bg-white py-1 shadow-lg">
          <div className="flex items-center gap-2 border-b border-stone-100 px-3 py-2">
            <UserIcon className="h-4 w-4 text-stone-400" strokeWidth={1.75} />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-stone-900">{user.full_name || "Your account"}</p>
              <p className="truncate text-xs text-stone-500">{user.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            disabled={logoutMutation.isPending}
            className="flex w-full items-center gap-2 px-3 py-2 text-sm text-stone-700 hover:bg-stone-50 disabled:opacity-60"
          >
            <LogOut className="h-4 w-4" strokeWidth={1.75} />
            Log out
          </button>
        </div>
      )}
    </div>
  );
}

import { NavLink, useLocation } from "react-router-dom";
import { HardDrive, Users, Star, Trash2, Cloud } from "lucide-react";

const navItems = [
  { to: "/", label: "My Drive", icon: HardDrive, matchPrefix: "/folder" },
  { to: "/shared", label: "Shared with me", icon: Users },
  { to: "/starred", label: "Starred", icon: Star },
  { to: "/trash", label: "Trash", icon: Trash2 },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col border-r border-stone-200 bg-white">
      <div className="flex items-center gap-2 px-6 py-5">
        <Cloud className="h-5 w-5 text-teal-700" strokeWidth={1.75} />
        <span className="text-[15px] font-medium text-stone-900">Cloud Storage</span>
      </div>

      <nav className="flex flex-col gap-1 px-3">
        {navItems.map(({ to, label, icon: Icon, matchPrefix }) => {
          const isActive = to === "/" ? location.pathname === "/" || location.pathname.startsWith(matchPrefix || "\0") : location.pathname.startsWith(to);
          return (
            <NavLink
              key={to}
              to={to}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                isActive ? "bg-teal-50 text-teal-800" : "text-stone-600 hover:bg-stone-50 hover:text-stone-900"
              }`}
            >
              <Icon className="h-4 w-4" strokeWidth={1.75} />
              {label}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}

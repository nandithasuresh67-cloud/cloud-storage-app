import { NavLink, useLocation } from "react-router-dom";
import { HardDrive, Users, Star, Trash2, Cloud, X } from "lucide-react";

const navItems = [
  { to: "/", label: "My Drive", icon: HardDrive, matchPrefix: "/folder" },
  { to: "/shared", label: "Shared with me", icon: Users },
  { to: "/starred", label: "Starred", icon: Star },
  { to: "/trash", label: "Trash", icon: Trash2 },
];

export default function Sidebar({ mobileOpen = false, onClose = () => {} }) {
  const location = useLocation();

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 flex w-64 shrink-0 flex-col border-r border-stone-200 bg-white shadow-xl transition-transform duration-200 md:static md:z-auto md:min-h-screen md:w-56 md:translate-x-0 md:shadow-none lg:w-64 ${
        mobileOpen ? "translate-x-0" : "-translate-x-full"
      }`}
    >
      <div className="flex items-center justify-between gap-2 px-6 py-5">
        <div className="flex items-center gap-2">
          <Cloud className="h-5 w-5 text-teal-700" strokeWidth={1.75} />
          <span className="text-[15px] font-medium text-stone-900">Cloud Storage</span>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-1.5 text-stone-400 hover:bg-stone-100 hover:text-stone-700 md:hidden"
          aria-label="Close navigation"
        >
          <X className="h-5 w-5" strokeWidth={1.75} />
        </button>
      </div>

      <nav className="flex flex-col gap-1 px-3">
        {navItems.map(({ to, label, icon: Icon, matchPrefix }) => {
          const isActive = to === "/" ? location.pathname === "/" || location.pathname.startsWith(matchPrefix || "\0") : location.pathname.startsWith(to);
          return (
            <NavLink
              key={to}
              to={to}
              onClick={onClose}
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

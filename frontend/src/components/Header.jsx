import { useEffect, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { Search, X } from "lucide-react";
import ConnectionStatus from "./ConnectionStatus";
import UserMenu from "./UserMenu";

const DEBOUNCE_MS = 300;

export default function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [value, setValue] = useState(location.pathname === "/search" ? searchParams.get("q") || "" : "");

  // Keep the input in sync if the URL changes from elsewhere (back/forward, clearing on the results page).
  useEffect(() => {
    if (location.pathname === "/search") {
      setValue(searchParams.get("q") || "");
    } else {
      setValue("");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  useEffect(() => {
    const trimmed = value.trim();
    const timer = setTimeout(() => {
      if (trimmed) {
        navigate(`/search?q=${encodeURIComponent(trimmed)}`, { replace: location.pathname === "/search" });
      } else if (location.pathname === "/search") {
        navigate("/");
      }
    }, DEBOUNCE_MS);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <header className="flex items-center justify-between border-b border-stone-200 bg-white px-6 py-3">
      <div className="flex w-full max-w-md items-center gap-2 rounded-lg border border-stone-200 bg-stone-50 px-3 py-2">
        <Search className="h-4 w-4 shrink-0 text-stone-400" strokeWidth={1.75} />
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Search files and folders"
          className="w-full bg-transparent text-sm text-stone-700 placeholder:text-stone-400 focus:outline-none"
        />
        {value && (
          <button onClick={() => setValue("")} className="shrink-0 text-stone-400 hover:text-stone-600" aria-label="Clear search">
            <X className="h-3.5 w-3.5" strokeWidth={1.75} />
          </button>
        )}
      </div>
      <div className="flex items-center gap-3">
        <ConnectionStatus />
        <UserMenu />
      </div>
    </header>
  );
}

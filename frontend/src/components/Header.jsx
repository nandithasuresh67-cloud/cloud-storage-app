import { Search } from "lucide-react";
import ConnectionStatus from "./ConnectionStatus";
import UserMenu from "./UserMenu";

export default function Header() {
  return (
    <header className="flex items-center justify-between border-b border-stone-200 bg-white px-6 py-3">
      <div className="flex w-full max-w-md items-center gap-2 rounded-lg border border-stone-200 bg-stone-50 px-3 py-2">
        <Search className="h-4 w-4 text-stone-400" strokeWidth={1.75} />
        <input
          type="text"
          placeholder="Search files and folders"
          className="w-full bg-transparent text-sm text-stone-700 placeholder:text-stone-400 focus:outline-none"
          disabled
        />
      </div>
      <div className="flex items-center gap-3">
        <ConnectionStatus />
        <UserMenu />
      </div>
    </header>
  );
}

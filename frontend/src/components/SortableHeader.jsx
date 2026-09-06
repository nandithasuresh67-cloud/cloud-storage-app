import { ArrowDown, ArrowUp } from "lucide-react";

export default function SortableHeader({ label, sortKey, currentSort, onSort, className = "" }) {
  const isActive = currentSort.sortBy === sortKey;
  const nextOrder = isActive && currentSort.sortOrder === "asc" ? "desc" : "asc";

  return (
    <th className={`px-4 py-2.5 font-medium ${className}`}>
      <button
        onClick={() => onSort(sortKey, nextOrder)}
        className={`flex items-center gap-1 hover:text-stone-700 ${isActive ? "text-stone-700" : ""}`}
      >
        {label}
        {isActive &&
          (currentSort.sortOrder === "asc" ? (
            <ArrowUp className="h-3 w-3" strokeWidth={2} />
          ) : (
            <ArrowDown className="h-3 w-3" strokeWidth={2} />
          ))}
      </button>
    </th>
  );
}

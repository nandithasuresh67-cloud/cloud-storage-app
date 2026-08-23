import { ChevronRight } from "lucide-react";

export default function Breadcrumb({ path = [] }) {
  return (
    <div className="mb-4 flex items-center gap-1.5 text-sm text-stone-500">
      {path.map((segment, i) => (
        <span key={segment} className="flex items-center gap-1.5">
          <span className={i === path.length - 1 ? "font-medium text-stone-900" : ""}>
            {segment}
          </span>
          {i < path.length - 1 && <ChevronRight className="h-3.5 w-3.5" />}
        </span>
      ))}
    </div>
  );
}

import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";

/**
 * `items` is an array of { label, to } - `to` omitted (or falsy) on the
 * last item renders it as plain text instead of a link, since you're
 * already there.
 */
export default function Breadcrumb({ items = [] }) {
  return (
    <div className="mb-4 flex items-center gap-1.5 text-sm text-stone-500">
      {items.map((item, i) => {
        const isLast = i === items.length - 1;
        return (
          <span key={item.to || item.label} className="flex items-center gap-1.5">
            {isLast || !item.to ? (
              <span className={isLast ? "font-medium text-stone-900" : ""}>{item.label}</span>
            ) : (
              <Link to={item.to} className="hover:text-stone-900 hover:underline">
                {item.label}
              </Link>
            )}
            {!isLast && <ChevronRight className="h-3.5 w-3.5" />}
          </span>
        );
      })}
    </div>
  );
}

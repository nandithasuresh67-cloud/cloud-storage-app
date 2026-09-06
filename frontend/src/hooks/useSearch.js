import { useQuery } from "@tanstack/react-query";
import { search } from "../services/search";

export function useSearch(q, { itemType } = {}) {
  const trimmed = q?.trim();
  return useQuery({
    queryKey: ["search", trimmed, itemType],
    queryFn: () => search({ q: trimmed, itemType }),
    enabled: Boolean(trimmed),
  });
}

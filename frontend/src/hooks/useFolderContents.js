import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { createFolder, getFolderContents } from "../services/folders";

const PAGE_SIZE = 25;

/**
 * Server-side sorted + paginated. Sorting client-side after a partial
 * fetch would only ever reorder whatever page happened to be loaded so
 * far - correct-looking on a small folder, silently wrong on a large
 * one. `sortBy`/`sortOrder` are part of the query key, so changing sort
 * order starts pagination over from the first page rather than trying to
 * re-sort pages that were fetched under a different order.
 */
export function useFolderContents(folderId, { sortBy = "name", sortOrder = "asc" } = {}) {
  const query = useInfiniteQuery({
    queryKey: ["folder-contents", folderId || "root", sortBy, sortOrder],
    queryFn: ({ pageParam }) => getFolderContents(folderId, { sortBy, sortOrder, limit: PAGE_SIZE, offset: pageParam }),
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      const nextOffset = allPages.length * PAGE_SIZE;
      const hasMore = nextOffset < lastPage.subfolders_total || nextOffset < lastPage.files_total;
      return hasMore ? nextOffset : undefined;
    },
  });

  const pages = query.data?.pages || [];
  const firstPage = pages[0];

  return {
    ...query,
    folder: firstPage?.folder ?? null,
    breadcrumb: firstPage?.breadcrumb ?? [],
    subfolders: pages.flatMap((p) => p.subfolders),
    files: pages.flatMap((p) => p.files),
    subfoldersTotal: firstPage?.subfolders_total ?? 0,
    filesTotal: firstPage?.files_total ?? 0,
  };
}

export function useCreateFolder(folderId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name) => createFolder({ name, parentId: folderId }),
    onSuccess: () => {
      // Invalidate every sort variant for this folder, not just whichever one is currently active.
      queryClient.invalidateQueries({ queryKey: ["folder-contents", folderId || "root"] });
    },
  });
}

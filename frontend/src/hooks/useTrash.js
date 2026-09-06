import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { deleteFile } from "../services/files";
import { deleteFolder } from "../services/folders";
import { getTrash, permanentlyDeleteTrashItem, restoreTrashItem } from "../services/trash";

export function useTrash() {
  return useQuery({
    queryKey: ["trash"],
    queryFn: getTrash,
  });
}

export function useRestoreTrashItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ type, id }) => restoreTrashItem(type, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trash"] });
      queryClient.invalidateQueries({ queryKey: ["folder-contents"] });
    },
  });
}

export function usePermanentlyDeleteTrashItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ type, id }) => permanentlyDeleteTrashItem(type, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trash"] });
    },
  });
}

/**
 * Soft-delete from the active Drive listing. The backend moves the item to
 * Trash; the actual storage object remains available until permanent delete.
 */
export function useDeleteDriveItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ type, id }) => (type === "folder" ? deleteFolder(id) : deleteFile(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["folder-contents"] });
      queryClient.invalidateQueries({ queryKey: ["trash"] });
    },
  });
}

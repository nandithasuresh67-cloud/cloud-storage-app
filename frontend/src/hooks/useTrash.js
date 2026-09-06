import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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

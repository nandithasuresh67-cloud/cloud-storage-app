import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFolder, getFolderContents } from "../services/folders";

export function useFolderContents(folderId) {
  return useQuery({
    queryKey: ["folder-contents", folderId || "root"],
    queryFn: () => getFolderContents(folderId),
  });
}

export function useCreateFolder(folderId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name) => createFolder({ name, parentId: folderId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["folder-contents", folderId || "root"] });
    },
  });
}

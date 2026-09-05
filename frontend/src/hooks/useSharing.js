import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createShare, getSharedWithMe, listShares, revokeShare } from "../services/shares";
import { createPublicLink, listPublicLinks, revokePublicLink } from "../services/publicLinks";

export function useSharedWithMe() {
  return useQuery({
    queryKey: ["shared-with-me"],
    queryFn: getSharedWithMe,
  });
}

function targetKey(fileId, folderId) {
  return fileId ? ["file", fileId] : ["folder", folderId];
}

export function useShares(target) {
  const { fileId, folderId } = target;
  return useQuery({
    queryKey: ["shares", ...targetKey(fileId, folderId)],
    queryFn: () => listShares({ fileId, folderId }),
    enabled: Boolean(fileId || folderId),
  });
}

export function useCreateShare(target) {
  const queryClient = useQueryClient();
  const { fileId, folderId } = target;
  return useMutation({
    mutationFn: ({ email, role }) => createShare({ fileId, folderId, email, role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["shares", ...targetKey(fileId, folderId)] });
    },
  });
}

export function useRevokeShare(target) {
  const queryClient = useQueryClient();
  const { fileId, folderId } = target;
  return useMutation({
    mutationFn: (shareId) => revokeShare(shareId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["shares", ...targetKey(fileId, folderId)] });
    },
  });
}

export function usePublicLinks(target) {
  const { fileId, folderId } = target;
  return useQuery({
    queryKey: ["public-links", ...targetKey(fileId, folderId)],
    queryFn: () => listPublicLinks({ fileId, folderId }),
    enabled: Boolean(fileId || folderId),
  });
}

export function useCreatePublicLink(target) {
  const queryClient = useQueryClient();
  const { fileId, folderId } = target;
  return useMutation({
    mutationFn: ({ expiresInHours, password } = {}) =>
      createPublicLink({ fileId, folderId, expiresInHours, password }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["public-links", ...targetKey(fileId, folderId)] });
    },
  });
}

export function useRevokePublicLink(target) {
  const queryClient = useQueryClient();
  const { fileId, folderId } = target;
  return useMutation({
    mutationFn: (linkId) => revokePublicLink(linkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["public-links", ...targetKey(fileId, folderId)] });
    },
  });
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getMe, login, logout, register } from "../services/auth";

/**
 * Current-user query. 401 is an expected, normal outcome here (not
 * logged in yet) - retry is disabled so a logged-out visitor doesn't
 * cause three quiet retries against the API before settling.
 */
export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: getMe,
    retry: false,
    staleTime: 60_000,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: login,
    onSuccess: (user) => {
      queryClient.setQueryData(["me"], user);
    },
  });
}

export function useRegister() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: register,
    onSuccess: (user) => {
      queryClient.setQueryData(["me"], user);
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.setQueryData(["me"], null);
      queryClient.clear(); // drop any cached files/folders - they belonged to the now-logged-out user
    },
  });
}

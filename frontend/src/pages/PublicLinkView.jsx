import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Cloud, Download, File as FileIcon, Loader2, Lock } from "lucide-react";
import FileTypeIcon from "../components/FileTypeIcon";
import { accessPublicLink } from "../services/publicLinks";
import { formatBytes } from "../utils/format";

/**
 * Public, unauthenticated page for a shared link - the "Public User"
 * access path. Not wrapped in ProtectedRoute or GuestRoute: works whether
 * or not the visitor has an account or is logged in.
 */
export default function PublicLinkView() {
  const { token } = useParams();
  const [password, setPassword] = useState("");

  const accessMutation = useMutation({
    mutationFn: (pw) => accessPublicLink(token, pw),
  });
  const { mutate } = accessMutation;

  // Try without a password as soon as the page loads.
  useEffect(() => {
    mutate(undefined);
  }, [mutate]);

  const needsPassword = accessMutation.error?.response?.status === 401;
  const notFound = accessMutation.error?.response?.status === 404;
  const expired = accessMutation.error?.response?.status === 410;
  const errorDetail = accessMutation.error?.response?.data?.detail;

  function handlePasswordSubmit(e) {
    e.preventDefault();
    accessMutation.mutate(password);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-stone-50 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 flex items-center justify-center gap-2">
          <Cloud className="h-6 w-6 text-teal-700" strokeWidth={1.75} />
          <span className="text-lg font-medium text-stone-900">Cloud Storage</span>
        </div>

        <div className="rounded-xl border border-stone-200 bg-white p-8 shadow-sm">
          {accessMutation.isPending && (
            <div className="flex justify-center py-6">
              <Loader2 className="h-6 w-6 animate-spin text-stone-400" />
            </div>
          )}

          {needsPassword && (
            <form onSubmit={handlePasswordSubmit} className="flex flex-col items-center gap-4 py-2 text-center">
              <Lock className="h-8 w-8 text-stone-300" strokeWidth={1.5} />
              <p className="text-sm text-stone-600">This link is password-protected.</p>
              <input
                type="password"
                autoFocus
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                className="w-full rounded-lg border border-stone-300 px-3 py-2 text-center text-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600"
              />
              {password && errorDetail && <p className="text-xs text-red-600">{errorDetail}</p>}
              <button
                type="submit"
                className="w-full rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800"
              >
                Unlock
              </button>
            </form>
          )}

          {notFound && (
            <p className="py-6 text-center text-sm text-stone-500">
              This link doesn't exist or has been revoked.
            </p>
          )}

          {expired && <p className="py-6 text-center text-sm text-stone-500">This link has expired.</p>}

          {accessMutation.isSuccess && accessMutation.data.type === "file" && (
            <div className="flex flex-col items-center gap-3 py-2 text-center">
              <FileTypeIcon mimeType={accessMutation.data.mime_type} className="h-10 w-10 text-stone-400" />
              <p className="font-medium text-stone-900">{accessMutation.data.name}</p>
              <p className="text-sm text-stone-500">{formatBytes(accessMutation.data.size_bytes)}</p>
              {accessMutation.data.download_url ? (
                <a
                  href={accessMutation.data.download_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 flex items-center gap-2 rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800"
                >
                  <Download className="h-4 w-4" strokeWidth={1.75} />
                  Download
                </a>
              ) : (
                <p className="text-xs text-stone-400">This file's upload hasn't finished yet.</p>
              )}
            </div>
          )}

          {accessMutation.isSuccess && accessMutation.data.type === "folder" && (
            <div className="py-2">
              <p className="mb-4 text-center font-medium text-stone-900">{accessMutation.data.name}</p>
              <ul className="flex flex-col gap-1">
                {accessMutation.data.entries.map((entry) => (
                  <li key={entry.id} className="flex items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm text-stone-700">
                    <FileIcon className="h-4 w-4 shrink-0 text-stone-400" strokeWidth={1.75} />
                    {entry.name}
                  </li>
                ))}
                {accessMutation.data.entries.length === 0 && (
                  <li className="text-center text-sm text-stone-400">This folder is empty.</li>
                )}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

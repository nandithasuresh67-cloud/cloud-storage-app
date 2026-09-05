import { useState } from "react";
import { Check, Copy, Globe, Loader2, Trash2, X } from "lucide-react";
import {
  useCreatePublicLink,
  useCreateShare,
  usePublicLinks,
  useRevokePublicLink,
  useRevokeShare,
  useShares,
} from "../hooks/useSharing";

/**
 * `target` is { fileId } or { folderId } (exactly one) - same shape the
 * backend's sharing endpoints expect. `resourceName` is just for the
 * modal title.
 */
export default function ShareModal({ target, resourceName, onClose }) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("viewer");
  const [copied, setCopied] = useState(false);

  const sharesQuery = useShares(target);
  const createShareMutation = useCreateShare(target);
  const revokeShareMutation = useRevokeShare(target);

  const publicLinksQuery = usePublicLinks(target);
  const createLinkMutation = useCreatePublicLink(target);
  const revokeLinkMutation = useRevokePublicLink(target);

  const activeLink = publicLinksQuery.data?.[0]; // one link per resource is all the UI surfaces, even though the API allows more

  function handleInvite(e) {
    e.preventDefault();
    if (!email.trim()) return;
    createShareMutation.mutate(
      { email: email.trim(), role },
      { onSuccess: () => setEmail("") }
    );
  }

  function handleCopyLink() {
    if (!activeLink) return;
    const url = `${window.location.origin}/shared-link/${activeLink.token}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  const inviteError = createShareMutation.error?.response?.data?.detail;
  const linkError = createLinkMutation.error?.response?.data?.detail;

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-stone-900/40 px-4" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-xl bg-white p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-1 flex items-center justify-between">
          <h2 className="text-base font-medium text-stone-900">Share "{resourceName}"</h2>
          <button onClick={onClose} className="text-stone-400 hover:text-stone-600" aria-label="Close">
            <X className="h-4 w-4" strokeWidth={1.75} />
          </button>
        </div>

        {/* Invite by email */}
        <form onSubmit={handleInvite} className="mt-4 flex gap-2">
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter an email address"
            className="min-w-0 flex-1 rounded-lg border border-stone-300 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600"
          />
          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="rounded-lg border border-stone-300 px-2 py-2 text-sm text-stone-700 focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600"
          >
            <option value="viewer">Viewer</option>
            <option value="editor">Editor</option>
          </select>
          <button
            type="submit"
            disabled={!email.trim() || createShareMutation.isPending}
            className="flex items-center gap-1.5 rounded-lg bg-teal-700 px-3 py-2 text-sm font-medium text-white hover:bg-teal-800 disabled:opacity-60"
          >
            {createShareMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Invite
          </button>
        </form>
        {inviteError && <p className="mt-1.5 text-xs text-red-600">{inviteError}</p>}

        {/* Who has access */}
        <div className="mt-5">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-stone-400">Who has access</p>
          {sharesQuery.isLoading && <Loader2 className="h-4 w-4 animate-spin text-stone-400" />}
          {sharesQuery.data?.length === 0 && (
            <p className="text-sm text-stone-400">Only you have access right now.</p>
          )}
          <ul className="flex flex-col gap-1.5">
            {sharesQuery.data?.map((share) => (
              <li key={share.id} className="flex items-center justify-between rounded-lg px-1 py-1 text-sm">
                <div className="min-w-0">
                  <p className="truncate text-stone-800">{share.shared_with_email}</p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs capitalize text-stone-600">
                    {share.role}
                  </span>
                  <button
                    onClick={() => revokeShareMutation.mutate(share.id)}
                    disabled={revokeShareMutation.isPending}
                    className="text-stone-400 hover:text-red-600"
                    aria-label={`Remove ${share.shared_with_email}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" strokeWidth={1.75} />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Public link */}
        <div className="mt-5 border-t border-stone-100 pt-4">
          <p className="mb-2 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-stone-400">
            <Globe className="h-3.5 w-3.5" strokeWidth={1.75} />
            Public link
          </p>

          {publicLinksQuery.isLoading && <Loader2 className="h-4 w-4 animate-spin text-stone-400" />}

          {!publicLinksQuery.isLoading && !activeLink && (
            <button
              onClick={() => createLinkMutation.mutate({})}
              disabled={createLinkMutation.isPending}
              className="flex items-center gap-2 rounded-lg border border-stone-300 px-3 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50 disabled:opacity-60"
            >
              {createLinkMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              Create public link
            </button>
          )}

          {activeLink && (
            <div className="flex items-center gap-2">
              <input
                readOnly
                value={`${window.location.origin}/shared-link/${activeLink.token}`}
                className="min-w-0 flex-1 truncate rounded-lg border border-stone-200 bg-stone-50 px-3 py-2 text-xs text-stone-500"
              />
              <button
                onClick={handleCopyLink}
                className="shrink-0 rounded-lg border border-stone-300 p-2 text-stone-600 hover:bg-stone-50"
                aria-label="Copy link"
              >
                {copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" strokeWidth={1.75} />}
              </button>
              <button
                onClick={() => revokeLinkMutation.mutate(activeLink.id)}
                disabled={revokeLinkMutation.isPending}
                className="shrink-0 rounded-lg border border-stone-300 p-2 text-stone-600 hover:bg-red-50 hover:text-red-600"
                aria-label="Revoke link"
              >
                <Trash2 className="h-4 w-4" strokeWidth={1.75} />
              </button>
            </div>
          )}
          {activeLink?.has_password && (
            <p className="mt-1.5 text-xs text-stone-400">Password-protected.</p>
          )}
          {linkError && <p className="mt-1.5 text-xs text-red-600">{linkError}</p>}
        </div>
      </div>
    </div>
  );
}

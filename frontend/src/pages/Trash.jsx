import { useState } from "react";
import { AlertCircle, FileText, FolderOpen, Loader2, RotateCcw, Trash2 } from "lucide-react";
import Breadcrumb from "../components/Breadcrumb";
import EmptyState from "../components/EmptyState";
import FileTypeIcon from "../components/FileTypeIcon";
import { usePermanentlyDeleteTrashItem, useRestoreTrashItem, useTrash } from "../hooks/useTrash";
import { formatDate } from "../utils/format";

export default function Trash() {
  const { data, isLoading, isError, error, refetch } = useTrash();
  const restoreMutation = useRestoreTrashItem();
  const deleteMutation = usePermanentlyDeleteTrashItem();
  const [pendingDelete, setPendingDelete] = useState(null);

  function handleRestore(item) {
    restoreMutation.mutate({ type: item.type, id: item.id });
  }

  function handlePermanentDelete(item) {
    setPendingDelete(item);
  }

  function confirmPermanentDelete() {
    if (!pendingDelete) return;
    deleteMutation.mutate(
      { type: pendingDelete.type, id: pendingDelete.id },
      { onSuccess: () => setPendingDelete(null) }
    );
  }

  const mutationError = restoreMutation.error?.response?.data?.detail || deleteMutation.error?.response?.data?.detail;

  return (
    <div className="mx-auto w-full max-w-6xl">
      <Breadcrumb items={[{ label: "Trash" }]} />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-lg font-medium text-stone-900">Trash</h1>
          <p className="mt-1 text-sm text-stone-500">Restore items or permanently delete them.</p>
        </div>
        {data?.length > 0 && (
          <span className="self-start rounded-full bg-stone-100 px-3 py-1 text-xs font-medium text-stone-600">
            {data.length} item{data.length === 1 ? "" : "s"}
          </span>
        )}
      </div>

      {mutationError && (
        <div className="mb-4 flex items-start justify-between gap-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          <span>{mutationError}</span>
          <button onClick={() => { restoreMutation.reset(); deleteMutation.reset(); }} className="font-medium hover:underline">Dismiss</button>
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-24" role="status" aria-label="Loading trash">
          <Loader2 className="h-6 w-6 animate-spin text-stone-400" />
        </div>
      )}

      {isError && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-red-200 bg-red-50/50 py-20 text-center">
          <AlertCircle className="mb-4 h-8 w-8 text-red-400" strokeWidth={1.5} />
          <p className="text-sm font-medium text-stone-800">Couldn't load Trash</p>
          <p className="mt-1 max-w-sm text-sm text-stone-500">
            {error?.response?.data?.detail || "Something went wrong while loading your deleted items."}
          </p>
          <button onClick={() => refetch()} className="mt-4 rounded-lg border border-stone-300 bg-white px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50">
            Try again
          </button>
        </div>
      )}

      {data && data.length === 0 && (
        <EmptyState
          icon={Trash2}
          title="Trash is empty"
          description="Deleted files and folders will stay here until you restore or permanently delete them."
        />
      )}

      {data && data.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-stone-200 bg-white">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[620px] text-left text-sm">
              <thead>
                <tr className="border-b border-stone-200 bg-stone-50 text-xs font-medium uppercase tracking-wide text-stone-500">
                  <th className="px-4 py-2.5 font-medium">Name</th>
                  <th className="px-4 py-2.5 font-medium">Type</th>
                  <th className="px-4 py-2.5 font-medium">Deleted</th>
                  <th className="px-4 py-2.5 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {data.map((item) => {
                  const isRestoring = restoreMutation.isPending && restoreMutation.variables?.id === item.id;
                  const isDeleting = deleteMutation.isPending && deleteMutation.variables?.id === item.id;
                  return (
                    <tr key={`${item.type}-${item.id}`} className="group hover:bg-stone-50">
                      <td className="px-4 py-3 text-stone-800">
                        <div className="flex min-w-0 items-center gap-2.5">
                          {item.type === "folder" ? (
                            <FolderOpen className="h-4 w-4 shrink-0 text-teal-700" strokeWidth={1.75} />
                          ) : (
                            <FileTypeIcon mimeType={null} className="h-4 w-4 shrink-0 text-stone-400" />
                          )}
                          <span className="truncate">{item.name}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 capitalize text-stone-500">
                        <span className="inline-flex items-center gap-1.5">
                          {item.type === "folder" ? <FolderOpen className="h-3.5 w-3.5" /> : <FileText className="h-3.5 w-3.5" />}
                          {item.type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-stone-500">{formatDate(item.trashed_at)}</td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => handleRestore(item)}
                            disabled={isRestoring || isDeleting || deleteMutation.isPending}
                            className="inline-flex items-center gap-1.5 rounded-lg border border-stone-300 bg-white px-3 py-1.5 text-xs font-medium text-stone-700 hover:bg-stone-100 disabled:cursor-not-allowed disabled:opacity-50"
                            aria-label={`Restore ${item.name}`}
                          >
                            {isRestoring ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RotateCcw className="h-3.5 w-3.5" />}
                            Restore
                          </button>
                          <button
                            onClick={() => handlePermanentDelete(item)}
                            disabled={isRestoring || isDeleting || restoreMutation.isPending}
                            className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 bg-white px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
                            aria-label={`Permanently delete ${item.name}`}
                          >
                            {isDeleting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
                            Delete forever
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {pendingDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title">
          <div className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl">
            <h2 id="delete-dialog-title" className="text-base font-semibold text-stone-900">Delete forever?</h2>
            <p className="mt-2 text-sm leading-6 text-stone-600">
              <span className="font-medium text-stone-800">{pendingDelete.name}</span> will be permanently deleted. This action cannot be undone.
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button onClick={() => setPendingDelete(null)} disabled={deleteMutation.isPending} className="rounded-lg border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50">
                Cancel
              </button>
              <button onClick={confirmPermanentDelete} disabled={deleteMutation.isPending} className="flex items-center gap-2 rounded-lg bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-800 disabled:opacity-60">
                {deleteMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Delete forever
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

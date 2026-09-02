import { AlertCircle, Check, Loader2, X } from "lucide-react";

const STATUS_LABEL = {
  queued: "Waiting…",
  starting: "Preparing…",
  uploading: "Uploading…",
  finishing: "Finishing…",
  done: "Uploaded",
  error: "Failed",
};

export default function UploadProgressPanel({ uploads, onDismiss }) {
  if (uploads.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-30 w-80 overflow-hidden rounded-xl border border-stone-200 bg-white shadow-lg">
      <div className="border-b border-stone-100 px-4 py-2.5 text-sm font-medium text-stone-700">
        {uploads.filter((u) => u.status !== "done" && u.status !== "error").length > 0
          ? "Uploading files…"
          : "Uploads"}
      </div>
      <ul className="max-h-72 overflow-y-auto">
        {uploads.map((u) => (
          <li key={u.clientId} className="flex items-start gap-3 px-4 py-2.5">
            <div className="mt-0.5 shrink-0">
              {u.status === "done" && <Check className="h-4 w-4 text-emerald-600" strokeWidth={2} />}
              {u.status === "error" && <AlertCircle className="h-4 w-4 text-red-600" strokeWidth={2} />}
              {u.status !== "done" && u.status !== "error" && (
                <Loader2 className="h-4 w-4 animate-spin text-teal-700" strokeWidth={2} />
              )}
            </div>

            <div className="min-w-0 flex-1">
              <p className="truncate text-sm text-stone-800">{u.name}</p>
              {u.status === "error" ? (
                <p className="text-xs text-red-600">{u.error}</p>
              ) : (
                <>
                  <p className="text-xs text-stone-500">{STATUS_LABEL[u.status]}</p>
                  {(u.status === "uploading" || u.status === "starting") && (
                    <div className="mt-1 h-1 w-full overflow-hidden rounded-full bg-stone-100">
                      <div
                        className="h-full rounded-full bg-teal-700 transition-all"
                        style={{ width: `${u.progress}%` }}
                      />
                    </div>
                  )}
                </>
              )}
            </div>

            {(u.status === "done" || u.status === "error") && (
              <button
                onClick={() => onDismiss(u.clientId)}
                className="mt-0.5 shrink-0 text-stone-400 hover:text-stone-600"
                aria-label="Dismiss"
              >
                <X className="h-3.5 w-3.5" strokeWidth={2} />
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

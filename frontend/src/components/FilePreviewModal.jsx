import { useQuery } from "@tanstack/react-query";
import { Download, Loader2, X } from "lucide-react";
import { getFile } from "../services/files";
import FileTypeIcon from "./FileTypeIcon";
import { formatBytes } from "../utils/format";

export default function FilePreviewModal({ fileId, onClose }) {
  const { data: file, isLoading, isError } = useQuery({
    queryKey: ["file", fileId],
    queryFn: () => getFile(fileId),
  });

  const isImage = file?.mime_type?.startsWith("image/");
  const isPdf = file?.mime_type === "application/pdf";
  const canPreviewInline = (isImage || isPdf) && file?.download_url;

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-stone-900/40 px-4" onClick={onClose}>
      <div
        className="flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden rounded-xl bg-white shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-stone-100 px-5 py-3">
          <div className="flex min-w-0 items-center gap-2">
            <FileTypeIcon mimeType={file?.mime_type} className="h-4 w-4 shrink-0 text-stone-500" />
            <h2 className="truncate text-sm font-medium text-stone-900">{file?.name || "Loading…"}</h2>
          </div>
          <button onClick={onClose} className="shrink-0 text-stone-400 hover:text-stone-600" aria-label="Close">
            <X className="h-4 w-4" strokeWidth={1.75} />
          </button>
        </div>

        <div className="flex flex-1 items-center justify-center overflow-auto bg-stone-50 p-4">
          {isLoading && <Loader2 className="h-6 w-6 animate-spin text-stone-400" />}

          {isError && <p className="text-sm text-stone-500">Couldn't load this file.</p>}

          {file && !file.download_url && (
            <p className="max-w-xs text-center text-sm text-stone-500">
              This file's upload hasn't finished, so there's nothing to preview or download yet.
            </p>
          )}

          {file && file.download_url && isImage && (
            <img src={file.download_url} alt={file.name} className="max-h-[60vh] max-w-full rounded-lg object-contain" />
          )}

          {file && file.download_url && isPdf && (
            <iframe src={file.download_url} title={file.name} className="h-[60vh] w-full rounded-lg bg-white" />
          )}

          {file && file.download_url && !canPreviewInline && (
            <div className="flex flex-col items-center gap-2 text-center">
              <FileTypeIcon mimeType={file.mime_type} className="h-10 w-10 text-stone-300" />
              <p className="text-sm text-stone-500">Preview isn't available for this file type.</p>
            </div>
          )}
        </div>

        {file && (
          <div className="flex items-center justify-between border-t border-stone-100 px-5 py-3">
            <span className="text-xs text-stone-500">{formatBytes(file.size_bytes)}</span>
            {file.download_url && (
              <a
                href={file.download_url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 rounded-lg bg-teal-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-teal-800"
              >
                <Download className="h-3.5 w-3.5" strokeWidth={1.75} />
                Download
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

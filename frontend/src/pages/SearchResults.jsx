import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { AlertCircle, FolderOpen, Loader2, SearchX } from "lucide-react";
import Breadcrumb from "../components/Breadcrumb";
import EmptyState from "../components/EmptyState";
import FileTypeIcon from "../components/FileTypeIcon";
import FilePreviewModal from "../components/FilePreviewModal";
import { useSearch } from "../hooks/useSearch";
import { formatBytes, formatDate } from "../utils/format";

export default function SearchResults() {
  const [searchParams] = useSearchParams();
  const q = searchParams.get("q") || "";
  const navigate = useNavigate();
  const [previewFileId, setPreviewFileId] = useState(null);
  const [itemType, setItemType] = useState(null); // null | "file" | "folder"

  const { data, isLoading, isError, error } = useSearch(q, { itemType });

  function handleRowClick(item) {
    if (item.type === "folder") navigate(`/folder/${item.id}`);
    else setPreviewFileId(item.id);
  }

  return (
    <div>
      <Breadcrumb items={[{ label: "My Drive", to: "/" }, { label: `Search results for "${q}"` }]} />

      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-lg font-medium text-stone-900">Search results for "{q}"</h1>
        <div className="flex items-center gap-1 rounded-lg border border-stone-200 p-0.5 text-sm">
          {[
            { value: null, label: "All" },
            { value: "folder", label: "Folders" },
            { value: "file", label: "Files" },
          ].map((opt) => (
            <button
              key={opt.label}
              onClick={() => setItemType(opt.value)}
              className={`rounded-md px-3 py-1 ${
                itemType === opt.value ? "bg-teal-700 text-white" : "text-stone-600 hover:bg-stone-50"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-24">
          <Loader2 className="h-6 w-6 animate-spin text-stone-400" />
        </div>
      )}

      {isError && (
        <EmptyState
          icon={AlertCircle}
          title="Search failed"
          description={error?.response?.data?.detail || "Something went wrong. Try again."}
        />
      )}

      {data && data.length === 0 && (
        <EmptyState icon={SearchX} title="No matches" description={`Nothing found for "${q}".`} />
      )}

      {data && data.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-stone-200">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-stone-200 bg-stone-50 text-xs font-medium uppercase tracking-wide text-stone-500">
                <th className="px-4 py-2.5 font-medium">Name</th>
                <th className="px-4 py-2.5 font-medium">Size</th>
                <th className="px-4 py-2.5 font-medium">Modified</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {data.map((item) => (
                <tr key={`${item.type}-${item.id}`} onClick={() => handleRowClick(item)} className="cursor-pointer hover:bg-stone-50">
                  <td className="flex items-center gap-2.5 px-4 py-2.5 text-stone-800">
                    {item.type === "folder" ? (
                      <FolderOpen className="h-4 w-4 shrink-0 text-teal-700" strokeWidth={1.75} />
                    ) : (
                      <FileTypeIcon mimeType={item.mime_type} className="h-4 w-4 shrink-0 text-stone-400" />
                    )}
                    {item.name}
                  </td>
                  <td className="px-4 py-2.5 text-stone-500">
                    {item.type === "file" ? formatBytes(item.size_bytes) : "—"}
                  </td>
                  <td className="px-4 py-2.5 text-stone-500">{formatDate(item.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {previewFileId && <FilePreviewModal fileId={previewFileId} onClose={() => setPreviewFileId(null)} />}
    </div>
  );
}

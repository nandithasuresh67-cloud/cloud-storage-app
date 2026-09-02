import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AlertCircle, FolderOpen, FolderPlus, Loader2, UploadCloud } from "lucide-react";
import Breadcrumb from "../components/Breadcrumb";
import EmptyState from "../components/EmptyState";
import FileTypeIcon from "../components/FileTypeIcon";
import NewFolderModal from "../components/NewFolderModal";
import { useCreateFolder, useFolderContents } from "../hooks/useFolderContents";
import { formatBytes, formatDate } from "../utils/format";

export default function Dashboard() {
  const { folderId } = useParams();
  const navigate = useNavigate();
  const [showNewFolder, setShowNewFolder] = useState(false);

  const { data, isLoading, isError, error } = useFolderContents(folderId);
  const createFolderMutation = useCreateFolder(folderId);

  const breadcrumbItems = [
    { label: "My Drive", to: "/" },
    ...(data?.breadcrumb || []).map((b) => ({ label: b.name, to: `/folder/${b.id}` })),
  ];

  function handleCreateFolder(name) {
    createFolderMutation.mutate(name, { onSuccess: () => setShowNewFolder(false) });
  }

  const isEmpty = data && data.subfolders.length === 0 && data.files.length === 0;

  return (
    <div>
      <Breadcrumb items={breadcrumbItems} />

      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-lg font-medium text-stone-900">
          {data?.folder ? data.folder.name : "My Drive"}
        </h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowNewFolder(true)}
            className="flex items-center gap-2 rounded-lg border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50"
          >
            <FolderPlus className="h-4 w-4" strokeWidth={1.75} />
            New folder
          </button>
          <button
            disabled
            className="flex items-center gap-2 rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white opacity-50"
            title="Upload UI lands on Day 10 - the backend upload API already works (see the Postman collection)"
          >
            <UploadCloud className="h-4 w-4" strokeWidth={1.75} />
            Upload
          </button>
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
          title="Couldn't load this folder"
          description={error?.response?.data?.detail || "Something went wrong. Try going back to My Drive."}
        />
      )}

      {data && isEmpty && (
        <EmptyState
          icon={FolderOpen}
          title="No files yet"
          description="Create a folder to get organized, or check back once file upload lands."
        />
      )}

      {data && !isEmpty && (
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
              {data.subfolders.map((folder) => (
                <tr
                  key={folder.id}
                  onClick={() => navigate(`/folder/${folder.id}`)}
                  className="cursor-pointer hover:bg-stone-50"
                >
                  <td className="flex items-center gap-2.5 px-4 py-2.5 text-stone-800">
                    <FolderOpen className="h-4 w-4 shrink-0 text-teal-700" strokeWidth={1.75} />
                    {folder.name}
                  </td>
                  <td className="px-4 py-2.5 text-stone-400">—</td>
                  <td className="px-4 py-2.5 text-stone-500">{formatDate(folder.updated_at)}</td>
                </tr>
              ))}
              {data.files.map((file) => (
                <tr key={file.id} className="hover:bg-stone-50">
                  <td className="flex items-center gap-2.5 px-4 py-2.5 text-stone-800">
                    <FileTypeIcon mimeType={file.mime_type} className="h-4 w-4 shrink-0 text-stone-400" />
                    {file.name}
                    {file.upload_status === "pending" && (
                      <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs text-amber-700">
                        upload incomplete
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-stone-500">{formatBytes(file.size_bytes)}</td>
                  <td className="px-4 py-2.5 text-stone-500">{formatDate(file.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showNewFolder && (
        <NewFolderModal
          onClose={() => setShowNewFolder(false)}
          onCreate={handleCreateFolder}
          isPending={createFolderMutation.isPending}
          error={createFolderMutation.error?.response?.data?.detail}
        />
      )}
    </div>
  );
}

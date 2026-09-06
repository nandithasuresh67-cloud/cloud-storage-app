import { useState } from "react";
import { useDropzone } from "react-dropzone";
import { useNavigate, useParams } from "react-router-dom";
import { AlertCircle, FolderOpen, FolderPlus, Loader2, Share2, UploadCloud } from "lucide-react";
import Breadcrumb from "../components/Breadcrumb";
import EmptyState from "../components/EmptyState";
import FilePreviewModal from "../components/FilePreviewModal";
import FileTypeIcon from "../components/FileTypeIcon";
import NewFolderModal from "../components/NewFolderModal";
import ShareModal from "../components/ShareModal";
import SortableHeader from "../components/SortableHeader";
import UploadProgressPanel from "../components/UploadProgressPanel";
import { useCreateFolder, useFolderContents } from "../hooks/useFolderContents";
import { useFileUpload } from "../hooks/useFileUpload";
import { formatBytes, formatDate } from "../utils/format";

export default function Dashboard() {
  const { folderId } = useParams();
  const navigate = useNavigate();
  const [showNewFolder, setShowNewFolder] = useState(false);
  const [previewFileId, setPreviewFileId] = useState(null);
  const [shareTarget, setShareTarget] = useState(null); // { fileId } | { folderId } | { fileId/folderId, name }
  const [sort, setSort] = useState({ sortBy: "name", sortOrder: "asc" });

  const {
    folder,
    breadcrumb,
    subfolders,
    files,
    subfoldersTotal,
    filesTotal,
    isLoading,
    isError,
    error,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
  } = useFolderContents(folderId, sort);
  const createFolderMutation = useCreateFolder(folderId);
  const { uploads, startUpload, dismissUpload } = useFileUpload(folderId);

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    noClick: true,
    noKeyboard: true,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) startUpload(acceptedFiles);
    },
  });

  const breadcrumbItems = [
    { label: "My Drive", to: "/" },
    ...breadcrumb.map((b) => ({ label: b.name, to: `/folder/${b.id}` })),
  ];

  function handleCreateFolder(name) {
    createFolderMutation.mutate(name, { onSuccess: () => setShowNewFolder(false) });
  }

  function handleFileRowClick(file) {
    if (file.upload_status === "uploaded") setPreviewFileId(file.id);
  }

  function openShareForFolder(e, folder) {
    e.stopPropagation();
    setShareTarget({ folderId: folder.id, name: folder.name });
  }

  function openShareForFile(e, file) {
    e.stopPropagation();
    setShareTarget({ fileId: file.id, name: file.name });
  }

  function handleSort(sortBy, sortOrder) {
    setSort({ sortBy, sortOrder });
  }

  const isEmpty = !isLoading && subfolders.length === 0 && files.length === 0;
  const loadedCount = subfolders.length + files.length;
  const totalCount = subfoldersTotal + filesTotal;

  return (
    <div {...getRootProps()} className="relative min-h-full outline-none">
      <input {...getInputProps()} />

      <Breadcrumb items={breadcrumbItems} />

      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-lg font-medium text-stone-900">{folder ? folder.name : "My Drive"}</h1>
        <div className="flex items-center gap-2">
          {folder && (
            <button
              onClick={() => setShareTarget({ folderId: folder.id, name: folder.name })}
              className="flex items-center gap-2 rounded-lg border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50"
            >
              <Share2 className="h-4 w-4" strokeWidth={1.75} />
              Share this folder
            </button>
          )}
          <button
            onClick={() => setShowNewFolder(true)}
            className="flex items-center gap-2 rounded-lg border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50"
          >
            <FolderPlus className="h-4 w-4" strokeWidth={1.75} />
            New folder
          </button>
          <button
            onClick={open}
            className="flex items-center gap-2 rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800"
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

      {isEmpty && (
        <EmptyState
          icon={FolderOpen}
          title="No files yet"
          description="Drag and drop files here, or use Upload, to add your first file."
        />
      )}

      {!isLoading && !isEmpty && (
        <>
          <div className="overflow-hidden rounded-xl border border-stone-200">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-stone-200 bg-stone-50 text-xs font-medium uppercase tracking-wide text-stone-500">
                  <SortableHeader label="Name" sortKey="name" currentSort={sort} onSort={handleSort} />
                  <SortableHeader label="Size" sortKey="size" currentSort={sort} onSort={handleSort} />
                  <SortableHeader label="Modified" sortKey="updated_at" currentSort={sort} onSort={handleSort} />
                  <th className="px-4 py-2.5 font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {subfolders.map((f) => (
                  <tr
                    key={f.id}
                    onClick={() => navigate(`/folder/${f.id}`)}
                    className="group cursor-pointer hover:bg-stone-50"
                  >
                    <td className="flex items-center gap-2.5 px-4 py-2.5 text-stone-800">
                      <FolderOpen className="h-4 w-4 shrink-0 text-teal-700" strokeWidth={1.75} />
                      {f.name}
                    </td>
                    <td className="px-4 py-2.5 text-stone-400">—</td>
                    <td className="px-4 py-2.5 text-stone-500">{formatDate(f.updated_at)}</td>
                    <td className="px-4 py-2.5 text-right">
                      <button
                        onClick={(e) => openShareForFolder(e, f)}
                        className="rounded-lg p-1.5 text-stone-400 opacity-0 hover:bg-stone-100 hover:text-stone-700 group-hover:opacity-100"
                        aria-label={`Share ${f.name}`}
                      >
                        <Share2 className="h-4 w-4" strokeWidth={1.75} />
                      </button>
                    </td>
                  </tr>
                ))}
                {files.map((file) => (
                  <tr
                    key={file.id}
                    onClick={() => handleFileRowClick(file)}
                    className={`group ${file.upload_status === "uploaded" ? "cursor-pointer hover:bg-stone-50" : "opacity-70"}`}
                    title={file.upload_status !== "uploaded" ? "Upload hasn't finished for this file yet" : undefined}
                  >
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
                    <td className="px-4 py-2.5 text-right">
                      <button
                        onClick={(e) => openShareForFile(e, file)}
                        className="rounded-lg p-1.5 text-stone-400 opacity-0 hover:bg-stone-100 hover:text-stone-700 group-hover:opacity-100"
                        aria-label={`Share ${file.name}`}
                      >
                        <Share2 className="h-4 w-4" strokeWidth={1.75} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {(hasNextPage || loadedCount > 0) && (
            <div className="mt-3 flex items-center justify-center gap-3 text-sm text-stone-500">
              {hasNextPage ? (
                <button
                  onClick={() => fetchNextPage()}
                  disabled={isFetchingNextPage}
                  className="flex items-center gap-2 rounded-lg border border-stone-300 px-4 py-1.5 font-medium text-stone-700 hover:bg-stone-50 disabled:opacity-60"
                >
                  {isFetchingNextPage && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                  Load more ({loadedCount} of {totalCount})
                </button>
              ) : (
                totalCount > 0 && <span>{totalCount} item{totalCount === 1 ? "" : "s"}</span>
              )}
            </div>
          )}
        </>
      )}

      {isDragActive && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center rounded-xl border-2 border-dashed border-teal-600 bg-teal-50/80">
          <p className="text-sm font-medium text-teal-800">Drop files to upload</p>
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

      {previewFileId && <FilePreviewModal fileId={previewFileId} onClose={() => setPreviewFileId(null)} />}

      {shareTarget && (
        <ShareModal target={shareTarget} resourceName={shareTarget.name} onClose={() => setShareTarget(null)} />
      )}

      <UploadProgressPanel uploads={uploads} onDismiss={dismissUpload} />
    </div>
  );
}

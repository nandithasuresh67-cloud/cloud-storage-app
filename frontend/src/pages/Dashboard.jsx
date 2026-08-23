import { UploadCloud, FolderOpen } from "lucide-react";
import Breadcrumb from "../components/Breadcrumb";
import EmptyState from "../components/EmptyState";

export default function Dashboard() {
  return (
    <div>
      <Breadcrumb path={["My Drive"]} />

      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-lg font-medium text-stone-900">My Drive</h1>
        <button
          disabled
          className="flex items-center gap-2 rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white opacity-50"
          title="Upload wiring lands on Day 3 (Object Storage) and Day 10 (Upload UI)"
        >
          <UploadCloud className="h-4 w-4" strokeWidth={1.75} />
          Upload
        </button>
      </div>

      <EmptyState
        icon={FolderOpen}
        title="No files yet"
        description="Drag and drop files here, or use Upload, once the file-upload flow is wired up in a later step."
      />
    </div>
  );
}

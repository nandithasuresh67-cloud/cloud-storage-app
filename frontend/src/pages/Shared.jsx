import { useNavigate } from "react-router-dom";
import { AlertCircle, FolderOpen, Loader2, Users } from "lucide-react";
import Breadcrumb from "../components/Breadcrumb";
import EmptyState from "../components/EmptyState";
import FileTypeIcon from "../components/FileTypeIcon";
import { useSharedWithMe } from "../hooks/useSharing";

export default function Shared() {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useSharedWithMe();

  function handleClick(item) {
    if (item.type === "folder") navigate(`/folder/${item.id}`);
    // Files shared directly don't have a dedicated route yet - opening a
    // preview modal from here isn't wired up (Day 11 is producing/
    // managing shares; a shared-item file browser is a natural follow-up,
    // not in this day's scope).
  }

  return (
    <div>
      <Breadcrumb items={[{ label: "Shared with me" }]} />
      <h1 className="mb-6 text-lg font-medium text-stone-900">Shared with me</h1>

      {isLoading && (
        <div className="flex items-center justify-center py-24">
          <Loader2 className="h-6 w-6 animate-spin text-stone-400" />
        </div>
      )}

      {isError && (
        <EmptyState icon={AlertCircle} title="Couldn't load shared items" description="Something went wrong. Try refreshing." />
      )}

      {data && data.length === 0 && (
        <EmptyState
          icon={Users}
          title="Nothing shared with you yet"
          description="Files and folders other people share with you will show up here."
        />
      )}

      {data && data.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-stone-200">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-stone-200 bg-stone-50 text-xs font-medium uppercase tracking-wide text-stone-500">
                <th className="px-4 py-2.5 font-medium">Name</th>
                <th className="px-4 py-2.5 font-medium">Your access</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {data.map((item) => (
                <tr
                  key={item.share_id}
                  onClick={() => handleClick(item)}
                  className={item.type === "folder" ? "cursor-pointer hover:bg-stone-50" : ""}
                >
                  <td className="flex items-center gap-2.5 px-4 py-2.5 text-stone-800">
                    {item.type === "folder" ? (
                      <FolderOpen className="h-4 w-4 shrink-0 text-teal-700" strokeWidth={1.75} />
                    ) : (
                      <FileTypeIcon mimeType={null} className="h-4 w-4 shrink-0 text-stone-400" />
                    )}
                    {item.name}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs capitalize text-stone-600">
                      {item.role}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

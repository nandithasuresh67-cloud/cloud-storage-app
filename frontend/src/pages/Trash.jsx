import { Trash2 } from "lucide-react";
import Breadcrumb from "../components/Breadcrumb";
import EmptyState from "../components/EmptyState";

export default function Trash() {
  return (
    <div>
      <Breadcrumb items={[{ label: "Trash" }]} />
      <h1 className="mb-6 text-lg font-medium text-stone-900">Trash</h1>
      <EmptyState
        icon={Trash2}
        title="Trash is empty"
        description="Deleted files and folders will stay here until you restore or permanently delete them."
      />
    </div>
  );
}

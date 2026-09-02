import { Users } from "lucide-react";
import Breadcrumb from "../components/Breadcrumb";
import EmptyState from "../components/EmptyState";

export default function Shared() {
  return (
    <div>
      <Breadcrumb items={[{ label: "Shared with me" }]} />
      <h1 className="mb-6 text-lg font-medium text-stone-900">Shared with me</h1>
      <EmptyState
        icon={Users}
        title="Nothing shared with you yet"
        description="Files and folders other people share with you will show up here, once sharing ships on Day 5 / Day 11."
      />
    </div>
  );
}

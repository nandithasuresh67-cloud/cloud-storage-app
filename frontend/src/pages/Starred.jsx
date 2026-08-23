import { Star } from "lucide-react";
import Breadcrumb from "../components/Breadcrumb";
import EmptyState from "../components/EmptyState";

export default function Starred() {
  return (
    <div>
      <Breadcrumb path={["Starred"]} />
      <h1 className="mb-6 text-lg font-medium text-stone-900">Starred</h1>
      <EmptyState
        icon={Star}
        title="No starred files"
        description="Star a file or folder to pin it here for quick access."
      />
    </div>
  );
}

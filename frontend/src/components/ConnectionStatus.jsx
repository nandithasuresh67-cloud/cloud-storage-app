import { useHealth } from "../hooks/useHealth";

export default function ConnectionStatus() {
  const { data, isLoading, isError } = useHealth();

  let label = "Checking backend…";
  let dotClass = "bg-stone-300";

  if (!isLoading) {
    if (isError) {
      label = "Backend unreachable";
      dotClass = "bg-red-500";
    } else if (data?.status === "healthy") {
      label = `Backend connected (${data.env})`;
      dotClass = "bg-emerald-500";
    }
  }

  return (
    <div className="flex items-center gap-2 rounded-full border border-stone-200 bg-white px-3 py-1.5 text-xs text-stone-600">
      <span className={`h-2 w-2 rounded-full ${dotClass}`} />
      {label}
    </div>
  );
}

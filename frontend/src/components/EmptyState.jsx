export default function EmptyState({ icon: Icon, title, description }) {
  return (
    <div className="flex h-full flex-col items-center justify-center rounded-xl border border-dashed border-stone-300 py-24 text-center">
      <Icon className="mb-4 h-8 w-8 text-stone-300" strokeWidth={1.5} />
      <p className="text-sm font-medium text-stone-700">{title}</p>
      <p className="mt-1 max-w-sm text-sm text-stone-500">{description}</p>
    </div>
  );
}

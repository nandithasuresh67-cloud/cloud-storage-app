import { Cloud } from "lucide-react";

export default function AuthLayout({ title, subtitle, children }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-stone-50 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex items-center justify-center gap-2">
          <Cloud className="h-6 w-6 text-teal-700" strokeWidth={1.75} />
          <span className="text-lg font-medium text-stone-900">Cloud Storage</span>
        </div>

        <div className="rounded-xl border border-stone-200 bg-white p-8 shadow-sm">
          <h1 className="text-lg font-medium text-stone-900">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-stone-500">{subtitle}</p>}
          <div className="mt-6">{children}</div>
        </div>
      </div>
    </div>
  );
}

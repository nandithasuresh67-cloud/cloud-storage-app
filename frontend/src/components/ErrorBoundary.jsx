import { Component } from "react";
import { AlertTriangle } from "lucide-react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    console.error("Unhandled frontend error:", error);
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <div className="flex min-h-screen items-center justify-center bg-stone-50 p-6 text-center">
        <div className="w-full max-w-md rounded-xl border border-stone-200 bg-white p-8 shadow-sm">
          <AlertTriangle className="mx-auto mb-4 h-8 w-8 text-amber-500" strokeWidth={1.5} />
          <h1 className="text-lg font-semibold text-stone-900">Something went wrong</h1>
          <p className="mt-2 text-sm text-stone-500">The application hit an unexpected error. Reload the page to continue.</p>
          <button onClick={() => window.location.reload()} className="mt-5 rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800">
            Reload application
          </button>
        </div>
      </div>
    );
  }
}

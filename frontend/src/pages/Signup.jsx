import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import AuthLayout from "../components/AuthLayout";
import { useRegister } from "../hooks/useAuth";

export default function Signup() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();
  const registerMutation = useRegister();

  function handleSubmit(e) {
    e.preventDefault();
    registerMutation.mutate(
      { email, password, fullName },
      { onSuccess: () => navigate("/", { replace: true }) }
    );
  }

  const errorMessage =
    registerMutation.isError &&
    (registerMutation.error?.response?.data?.detail || "Something went wrong. Please try again.");

  return (
    <AuthLayout title="Create an account" subtitle="Start storing and sharing your files">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label htmlFor="fullName" className="mb-1 block text-sm font-medium text-stone-700">
            Full name
          </label>
          <input
            id="fullName"
            type="text"
            autoComplete="name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600"
            placeholder="Jane Doe"
          />
        </div>

        <div>
          <label htmlFor="email" className="mb-1 block text-sm font-medium text-stone-700">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600"
            placeholder="you@example.com"
          />
        </div>

        <div>
          <label htmlFor="password" className="mb-1 block text-sm font-medium text-stone-700">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600"
            placeholder="At least 8 characters"
          />
        </div>

        {errorMessage && (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{errorMessage}</p>
        )}

        <button
          type="submit"
          disabled={registerMutation.isPending}
          className="mt-2 flex items-center justify-center gap-2 rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-teal-800 disabled:opacity-60"
        >
          {registerMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
          Sign up
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-stone-500">
        Already have an account?{" "}
        <Link to="/login" className="font-medium text-teal-700 hover:underline">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}

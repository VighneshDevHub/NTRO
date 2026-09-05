"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { AuthError, login, register } from "@/lib/auth";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "register") {
        await register(email, password);
      }
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof AuthError ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8">
          <p className="mb-1 font-mono text-xs uppercase tracking-widest text-muted">
            Case Access
          </p>
          <h1 className="text-2xl font-bold text-white">ForensicGuard</h1>
          <p className="mt-1 text-sm text-muted">
            Secure erasure &amp; forensic recovery platform
          </p>
        </div>

        <div className="border-l-2 border-amber bg-panel p-6">
          <div className="mb-5 flex gap-6 border-b border-line text-sm">
            <button
              type="button"
              onClick={() => setMode("login")}
              className={`-mb-px border-b-2 pb-2 font-medium ${
                mode === "login"
                  ? "border-amber text-amber"
                  : "border-transparent text-muted hover:text-gray-300"
              }`}
            >
              Sign in
            </button>
            <button
              type="button"
              onClick={() => setMode("register")}
              className={`-mb-px border-b-2 pb-2 font-medium ${
                mode === "register"
                  ? "border-amber text-amber"
                  : "border-transparent text-muted hover:text-gray-300"
              }`}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Operator email"
              className="border border-line bg-ink px-4 py-3 text-sm text-white placeholder-gray-500 focus:border-amber focus:outline-none"
            />
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password (min. 8 characters)"
              className="border border-line bg-ink px-4 py-3 text-sm text-white placeholder-gray-500 focus:border-amber focus:outline-none"
            />
            {error && <p className="text-sm text-alert">{error}</p>}
            <button
              type="submit"
              disabled={submitting}
              className="bg-amber px-4 py-3 text-sm font-medium text-ink hover:bg-amber-light disabled:opacity-50"
            >
              {submitting ? "Please wait…" : mode === "login" ? "Sign in" : "Register and sign in"}
            </button>
          </form>
        </div>

        <p className="mt-4 text-xs text-muted">
          Every record you submit is cryptographically tied to this
          account — the operator field can&apos;t be spoofed by client input.
        </p>
      </div>
    </main>
  );
}

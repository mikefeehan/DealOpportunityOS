"use client";

import { ReactNode, useEffect, useState } from "react";

// Client-side gate for the shared (static) deploy. A deterrent, not real
// security — pair with Vercel Deployment Protection for true access control.
const PASSWORD = "5120birch";
const KEY = "oos.auth";

export function PasswordGate({ children }: { children: ReactNode }) {
  const [authed, setAuthed] = useState(false);
  const [ready, setReady] = useState(false);
  const [value, setValue] = useState("");
  const [error, setError] = useState(false);

  useEffect(() => {
    setAuthed(typeof window !== "undefined" && window.localStorage.getItem(KEY) === PASSWORD);
    setReady(true);
  }, []);

  if (!ready) return null;
  if (authed) return <>{children}</>;

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (value === PASSWORD) {
      window.localStorage.setItem(KEY, PASSWORD);
      setAuthed(true);
    } else {
      setError(true);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6 terminal-grid">
      <form onSubmit={submit} className="w-full max-w-sm rounded-lg border border-border bg-panel p-6 shadow-terminal">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/brand/intrust-white.png" alt="InTrust Property Group" className="mx-auto mb-5 w-44" />
        <label className="text-xs uppercase tracking-wide text-muted">Password</label>
        <input
          type="password"
          value={value}
          autoFocus
          onChange={(e) => {
            setValue(e.target.value);
            setError(false);
          }}
          className="mt-1 h-10 w-full rounded-md border border-border bg-panel2 px-3 text-sm text-ink outline-none focus:border-amber/60"
          placeholder="Enter password"
        />
        {error && <div className="mt-2 text-sm text-red">Incorrect password.</div>}
        <button type="submit" className="mt-4 h-10 w-full rounded-md bg-amber font-medium text-white transition-opacity hover:opacity-90">
          Enter
        </button>
        <div className="mt-3 text-center text-xs text-muted">OpportunityOS · Acquisition Intelligence</div>
      </form>
    </div>
  );
}

'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { ApiError, api, type InteractiveBootPayload } from '@/lib/api';

interface Props {
  harness: string;
  artifactId: string;
}

function renderErrorDetail(error: unknown): string {
  if (error instanceof ApiError && error.detail) {
    return error.detail;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return 'Interactive route could not load its initial boot payload.';
}

export default function InteractiveSessionShell({ harness, artifactId }: Props) {
  const [payload, setPayload] = useState<InteractiveBootPayload | null>(null);
  const [errorDetail, setErrorDetail] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const nextPayload = await api.getSessionArtifactInteractiveBoot(harness, artifactId);
        if (!cancelled) {
          setPayload(nextPayload);
          setErrorDetail(null);
        }
      } catch (error) {
        if (!cancelled) {
          setPayload(null);
          setErrorDetail(renderErrorDetail(error));
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, [artifactId, harness]);

  if (errorDetail) {
    return (
      <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">
        <div className="mx-auto max-w-4xl rounded-3xl border border-rose-500/30 bg-slate-900/90 p-8 shadow-2xl shadow-slate-950/50">
          <p className="text-sm uppercase tracking-[0.3em] text-rose-300">Interactive Route</p>
          <h1 className="mt-3 text-3xl font-semibold text-white">Interactive session unavailable</h1>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">{errorDetail}</p>
          <div className="mt-8">
            <Link
              href={`/sessions/${encodeURIComponent(harness)}/${encodeURIComponent(artifactId)}`}
              className="inline-flex rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-200 transition hover:border-slate-500 hover:text-white"
            >
              Back to session dossier
            </Link>
          </div>
        </div>
      </main>
    );
  }

  if (!payload) {
    return (
      <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">
        <div className="mx-auto max-w-4xl rounded-3xl border border-slate-800 bg-slate-900/90 p-8 shadow-2xl shadow-slate-950/50">
          <p className="text-sm uppercase tracking-[0.3em] text-sky-300">Interactive Route</p>
          <h1 className="mt-3 text-3xl font-semibold text-white">Preparing interactive session</h1>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">
            Loading the backend boot payload, route identity, and the first honest interactive state for this
            session.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.12),_transparent_38%),linear-gradient(180deg,_#020617_0%,_#0f172a_100%)] px-6 py-10 text-slate-100">
      <div className="mx-auto max-w-5xl space-y-6">
        <header className="rounded-3xl border border-slate-800 bg-slate-900/90 p-8 shadow-2xl shadow-slate-950/50">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-3">
              <p className="text-sm uppercase tracking-[0.3em] text-sky-300">Interactive Route</p>
              <h1 className="text-3xl font-semibold text-white">Interactive session shell</h1>
              <p className="max-w-3xl text-sm leading-7 text-slate-300">{payload.interactive_session.detail}</p>
            </div>
            <Link
              href={payload.route.session_href}
              className="inline-flex rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-200 transition hover:border-slate-500 hover:text-white"
            >
              Back to session dossier
            </Link>
          </div>

          <dl className="mt-8 grid gap-4 md:grid-cols-3">
            <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <dt className="text-xs uppercase tracking-[0.24em] text-slate-400">Route state</dt>
              <dd className="mt-2 text-lg font-medium text-white">{payload.interactive_session.label}</dd>
              <dd className="mt-2 text-sm text-slate-300">{payload.session.status}</dd>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <dt className="text-xs uppercase tracking-[0.24em] text-slate-400">Transport</dt>
              <dd className="mt-2 text-lg font-medium text-white">{payload.runtime_identity.transport}</dd>
              <dd className="mt-2 text-sm text-slate-300">{payload.runtime_identity.thread_id}</dd>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <dt className="text-xs uppercase tracking-[0.24em] text-slate-400">Session</dt>
              <dd className="mt-2 text-lg font-medium text-white">{payload.session.session_id}</dd>
              <dd className="mt-2 text-sm text-slate-300">{payload.session.cwd || 'No cwd recorded'}</dd>
            </div>
          </dl>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <article className="rounded-3xl border border-slate-800 bg-slate-900/90 p-8 shadow-xl shadow-slate-950/40">
            <h2 className="text-xl font-semibold text-white">Tail snapshot</h2>
            <p className="mt-3 text-sm leading-7 text-slate-300">
              This shell keeps the route honest before live continuation is wired. The final route will replace this
              placeholder with the last visible session items.
            </p>
            {payload.tail.items.length === 0 ? (
              <div className="mt-6 rounded-2xl border border-dashed border-slate-700 bg-slate-950/60 p-5 text-sm text-slate-400">
                No tail snapshot yet. Replay handoff will fill this area in the next card.
              </div>
            ) : null}
          </article>

          <aside className="space-y-6">
            <article className="rounded-3xl border border-slate-800 bg-slate-900/90 p-6 shadow-xl shadow-slate-950/40">
              <h2 className="text-lg font-semibold text-white">Replay stream</h2>
              <p className="mt-3 text-sm leading-7 text-slate-300">
                Replay wiring is not attached yet. This shell exposes the route, capability state, and payload contract
                without pretending live history already streams in the browser.
              </p>
            </article>

            <article className="rounded-3xl border border-slate-800 bg-slate-900/90 p-6 shadow-xl shadow-slate-950/40">
              <h2 className="text-lg font-semibold text-white">Composer state</h2>
              <p className="mt-3 text-sm leading-7 text-slate-300">
                Composer controls stay intentionally inactive until the live timeline and state machine cards are
                delivered.
              </p>
            </article>
          </aside>
        </section>
      </div>
    </main>
  );
}

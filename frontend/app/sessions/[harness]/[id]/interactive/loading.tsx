export default function InteractiveSessionLoading() {
  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">
      <div className="mx-auto max-w-4xl rounded-3xl border border-slate-800 bg-slate-900/90 p-8 shadow-2xl shadow-slate-950/50">
        <p className="text-sm uppercase tracking-[0.3em] text-sky-300">Interactive Route</p>
        <h1 className="mt-3 text-3xl font-semibold text-white">Preparing interactive session</h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">
          Route-level loading is active while the interactive shell and backend boot payload are being prepared.
        </p>
      </div>
    </main>
  );
}

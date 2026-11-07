export default function Navbar({ health }) {
  const online = health?.status === "ok";
  return (
    <header className="sticky top-0 z-20 border-b border-white/10 bg-ink/75 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <a href="#top" className="flex items-center gap-2 font-semibold tracking-wide">
          <span className="grid h-8 w-8 place-items-center rounded-full border border-violet-300/40 bg-violet-500/20 text-sky-300">
            <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden="true">
              <circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" strokeWidth="1.8" />
              <path d="M12 2.5v3.2M12 18.3v3.2M2.5 12h3.2M18.3 12h3.2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          </span>
          LUMINA AI
        </a>
        <nav className="flex items-center gap-4 text-sm text-mist">
          <a className="hover:text-white" href="#studio">Studio</a>
          <a className="hidden hover:text-white sm:inline" href="#pipeline">Pipeline</a>
          <span
            className={`rounded-full border px-2.5 py-1 text-xs ${
              online
                ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-200"
                : "border-white/15 bg-white/5 text-mist"
            }`}
          >
            {online ? `API ${health.version}` : "API offline"}
          </span>
        </nav>
      </div>
    </header>
  );
}

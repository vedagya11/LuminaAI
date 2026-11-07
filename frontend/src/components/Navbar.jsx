import { Aperture } from "lucide-react";
import { GITHUB_URL } from "../links";

const LINKS = [
  ["Studio", "#studio"],
  ["Technology", "#technology"],
  ["Evaluation", "#evaluation"],
];

export default function Navbar({ health }) {
  const online = health?.status === "ok";
  return (
    <header className="sticky top-0 z-20 border-b border-line bg-bg">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <a href="#top" className="flex items-center gap-2 text-sm font-medium text-ink">
          <Aperture size={16} strokeWidth={1.75} className="text-accent" aria-hidden="true" />
          LUMINA AI
        </a>
        <nav className="hidden items-center gap-6 text-sm text-muted md:flex" aria-label="Primary">
          {LINKS.map(([label, href]) => (
            <a key={label} href={href} className="hover:text-ink">
              {label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <a
            href={GITHUB_URL}
            className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink"
            target="_blank"
            rel="noreferrer"
          >
            <GitHubMark />
            <span className="hidden sm:inline">GitHub</span>
          </a>
          <span className="inline-flex items-center gap-1.5 text-xs text-muted">
            <span className={`h-1.5 w-1.5 rounded-full ${online ? "bg-success" : "bg-danger"}`} />
            {online ? `API ${health.version}` : "API offline"}
          </span>
        </div>
      </div>
      <nav className="mx-auto flex max-w-6xl gap-5 px-4 pb-3 text-sm text-muted md:hidden" aria-label="Primary">
        {LINKS.map(([label, href]) => (
          <a key={label} href={href} className="hover:text-ink">
            {label}
          </a>
        ))}
      </nav>
    </header>
  );
}

function GitHubMark() {
  return (
    <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" aria-hidden="true" fill="currentColor">
      <path d="M8 0C3.58 0 0 3.58 0 8a8 8 0 0 0 5.47 7.59c.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.2 1.87.86 2.33.66.07-.52.28-.86.51-1.06-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.6 7.6 0 0 1 4 0c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z" />
    </svg>
  );
}

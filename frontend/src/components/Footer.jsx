import { GITHUB_URL } from "../links";

export default function Footer() {
  return (
    <footer className="mt-8 border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 text-sm text-muted sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-ink">LUMINA AI</p>
          <p className="mt-1">Bring Darkness to Light.</p>
        </div>
        <div className="sm:text-right">
          <p>React | FastAPI | OpenCV | PyTorch</p>
          <a href={GITHUB_URL} className="mt-1 inline-block text-ink hover:text-accent" target="_blank" rel="noreferrer">
            GitHub
          </a>
        </div>
      </div>
    </footer>
  );
}

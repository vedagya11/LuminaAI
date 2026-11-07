import { useState } from "react";

export default function Comparison({ beforeUrl, afterUrl }) {
  const [position, setPosition] = useState(50);

  return (
    <div className="border border-line bg-bg">
      <div className="relative">
        <img src={afterUrl} alt="Enhanced photograph" className="block max-h-[75vh] min-h-64 w-full object-contain" />
        <img
          src={beforeUrl}
          alt="Original photograph"
          className="absolute inset-0 h-full w-full object-contain"
          style={{ clipPath: `inset(0 ${100 - position}% 0 0)` }}
        />
        <div className="pointer-events-none absolute inset-y-0 w-px bg-ink" style={{ left: `${position}%` }} />
        <span className="absolute left-3 top-3 bg-panel px-2 py-1 text-xs text-muted">Original</span>
        <span className="absolute right-3 top-3 bg-panel px-2 py-1 text-xs text-muted">Enhanced</span>
      </div>
      <div className="border-t border-line px-4 py-3">
        <label className="block text-xs text-muted" htmlFor="compare">
          Before and after
        </label>
        <input
          id="compare"
          aria-label="Before and after comparison"
          type="range"
          min="0"
          max="100"
          value={position}
          onChange={(event) => setPosition(Number(event.target.value))}
          className="w-full"
        />
      </div>
    </div>
  );
}

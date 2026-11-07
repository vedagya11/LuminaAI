import { useState } from "react";

export default function Comparison({ beforeUrl, afterUrl }) {
  const [position, setPosition] = useState(56);

  return (
    <div className="mt-6 overflow-hidden rounded-3xl border border-white/10 bg-black">
      <div className="relative">
        <img src={afterUrl} alt="Enhanced photograph" className="block max-h-[70vh] w-full object-contain" />
        <img
          src={beforeUrl}
          alt="Original photograph"
          className="absolute inset-0 h-full w-full object-contain"
          style={{ clipPath: `inset(0 ${100 - position}% 0 0)` }}
        />
        <div
          className="pointer-events-none absolute inset-y-0 w-px bg-white/80"
          style={{ left: `${position}%` }}
        />
        <span className="absolute left-3 top-3 rounded-full bg-black/60 px-2 py-1 text-xs">Before</span>
        <span className="absolute right-3 top-3 rounded-full bg-black/60 px-2 py-1 text-xs">After</span>
      </div>
      <div className="px-4 py-3">
        <label className="block text-xs uppercase tracking-wider text-mist" htmlFor="compare">
          Before and after comparison
        </label>
        <input
          id="compare"
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

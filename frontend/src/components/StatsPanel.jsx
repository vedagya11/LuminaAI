export default function StatsPanel({ result }) {
  if (!result) {
    return (
      <section className="rounded-3xl border border-white/10 bg-charcoal/80 p-5">
        <h2 className="text-lg font-semibold">Processing statistics</h2>
        <p className="mt-2 text-sm text-mist">
          Measured luminance, contrast, noise, and processing time appear here after the API returns an enhanced image.
        </p>
      </section>
    );
  }

  const rows = [
    ["Processing time", `${result.processing_time_ms} ms`],
    ["Dimensions", `${result.width} × ${result.height}`],
    ["Mean luminance", `${result.input.mean_luminance} → ${result.output.mean_luminance}`],
    ["Contrast (stddev)", `${result.input.contrast_stddev} → ${result.output.contrast_stddev}`],
    ["Noise sigma", `${result.input.noise_sigma} → ${result.output.noise_sigma}`],
    ["Illumination gamma", String(result.gamma)],
    ["Output size", formatBytes(result.output_bytes)],
    ["Request", result.request_id],
  ];

  return (
    <section className="rounded-3xl border border-white/10 bg-charcoal/80 p-5">
      <h2 className="text-lg font-semibold">Processing statistics</h2>
      <p className="mt-1 text-sm text-mist">Computed from this image on the server. Nothing here is a fixed sample.</p>
      <dl className="mt-4 space-y-3">
        {rows.map(([label, value]) => (
          <div key={label} className="flex items-start justify-between gap-4 border-b border-white/5 pb-2 text-sm">
            <dt className="text-mist">{label}</dt>
            <dd className="max-w-[60%] break-all text-right text-white">{value}</dd>
          </div>
        ))}
      </dl>
      <ul className="mt-4 flex flex-wrap gap-2">
        {result.stages.map((stage) => (
          <li key={stage} className="rounded-full border border-sky-300/20 bg-sky-400/10 px-2.5 py-1 text-xs text-sky-100">
            {stage.replaceAll("_", " ")}
          </li>
        ))}
      </ul>
    </section>
  );
}

function formatBytes(size) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

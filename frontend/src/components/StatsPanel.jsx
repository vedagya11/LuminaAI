export default function StatsPanel({ result, original }) {
  const metrics = result?.available
    ? [
        ["Average luminance", change(result.input.mean_luminance, result.output.mean_luminance)],
        ["Contrast", change(result.input.contrast_stddev, result.output.contrast_stddev)],
        ["Noise estimate", change(result.input.noise_sigma, result.output.noise_sigma)],
        ["Saturation", result.no_reference ? String(result.no_reference.saturation_mean) : "—"],
        ["Processing time", result.processing_time_ms == null ? "—" : `${result.processing_time_ms} ms`],
        ["Image dimensions", `${result.width} × ${result.height}`],
      ]
    : [
        ["Average luminance", "—"],
        ["Contrast", "—"],
        ["Noise estimate", "—"],
        ["Saturation", "—"],
        ["Processing time", "—"],
        ["Image dimensions", "—"],
      ];

  return (
    <section id="evaluation" className="mx-auto max-w-6xl px-4 py-8">
      <h2 className="text-base font-medium">Evaluation</h2>
      <p className="mt-1 max-w-2xl text-sm text-muted">
        Values are measured on the selected result. PSNR and SSIM stay empty until a same-size reference is attached.
        {original?.mean_luminance != null ? ` Upload mean luminance ${original.mean_luminance}.` : ""}
      </p>
      <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {metrics.map(([label, value]) => (
          <article key={label} className="border border-line bg-card px-3 py-3 shadow-card">
            <p className="text-xs text-muted">{label}</p>
            <p className="mt-1 text-sm text-ink">{value}</p>
          </article>
        ))}
      </div>
      {result?.available && (
        <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="PSNR" value={fullReferencePsnr(result.full_reference)} />
          <Metric label="SSIM" value={result.full_reference?.ssim == null ? "Needs a reference" : String(result.full_reference.ssim)} />
          <Metric label="LPIPS" value={lpipsText(result.full_reference)} />
          <Metric label="NIQE" value={result.no_reference?.niqe == null ? "Not computed" : String(result.no_reference.niqe)} />
        </div>
      )}
      {result?.fusion_weights && (
        <p className="mt-3 text-sm text-muted">
          Fusion weights: classical {result.fusion_weights.classical_mean}, Zero-DCE++ {result.fusion_weights.deep_learning_mean}.
          Shadows {show(result.fusion_weights.deep_learning_dark_mean)}, highlights {show(result.fusion_weights.deep_learning_bright_mean)}.
        </p>
      )}
      {result?.stages?.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-1.5">
          {result.stages.map((stage) => (
            <li key={stage} className="border border-line px-2 py-1 text-xs text-muted">
              {stage.replaceAll("_", " ")}
            </li>
          ))}
        </ul>
      )}
      {result?.full_reference?.reason && <p className="mt-2 text-xs text-muted">{result.full_reference.reason}</p>}
      {result?.no_reference?.niqe_reason && <p className="mt-1 text-xs text-muted">{result.no_reference.niqe_reason}</p>}
      {result?.full_reference?.lpips_reason && <p className="mt-1 text-xs text-muted">{result.full_reference.lpips_reason}</p>}
    </section>
  );
}

function Metric({ label, value }) {
  return (
    <article className="border border-line bg-panel px-3 py-3">
      <p className="text-xs text-muted">{label}</p>
      <p className="mt-1 text-sm text-ink">{value}</p>
    </article>
  );
}

function change(before, after) {
  const delta = Math.round((after - before) * 100) / 100;
  const direction = delta > 0 ? "up" : delta < 0 ? "down" : "unchanged";
  return `${before} → ${after} (${direction} ${Math.abs(delta)})`;
}

function fullReferencePsnr(metrics) {
  if (!metrics || (!metrics.available && metrics.psnr == null)) return "Needs a reference";
  if (metrics.psnr_is_infinite) return "Infinite, identical to the reference";
  return metrics.psnr == null ? "Not computed" : `${metrics.psnr} dB`;
}

function lpipsText(metrics) {
  if (!metrics || metrics.lpips == null) return "Not computed";
  return String(metrics.lpips);
}

function show(value) {
  return value == null ? "n/a" : String(value);
}

export default function ResultGrid({ originalUrl, results, selected, onSelect }) {
  const enhanced = results.find((item) => item.method === selected && item.available && item.image_base64);
  const enhancedUrl = enhanced ? `data:${enhanced.media_type};base64,${enhanced.image_base64}` : "";

  return (
    <div>
      <div className="grid gap-3 lg:grid-cols-2">
        <figure className="border border-line bg-bg">
          <img src={originalUrl} alt="Original photograph" className="max-h-[75vh] min-h-64 w-full object-contain" />
          <figcaption className="border-t border-line px-3 py-2 text-xs text-muted">Original</figcaption>
        </figure>
        <figure className="border border-line bg-bg">
          {enhancedUrl ? (
            <img src={enhancedUrl} alt="Enhanced photograph" className="max-h-[75vh] min-h-64 w-full object-contain" />
          ) : (
            <p className="grid min-h-64 place-items-center px-4 text-sm text-muted">Select an available result.</p>
          )}
          <figcaption className="border-t border-line px-3 py-2 text-xs text-muted">
            {enhanced ? label(enhanced.method) : "Enhanced"}
            {enhanced?.processing_time_ms != null ? ` · ${enhanced.processing_time_ms} ms` : ""}
          </figcaption>
        </figure>
      </div>
      {results.length > 1 && (
        <div className="mt-3 grid gap-2 sm:grid-cols-3">
          {results.map((result) => {
            const url = result.available && result.image_base64 ? `data:${result.media_type};base64,${result.image_base64}` : "";
            return (
              <button
                key={result.method}
                type="button"
                disabled={!result.available}
                onClick={() => onSelect(result.method)}
                className={`border text-left ${selected === result.method ? "border-accent" : "border-line"} ${
                  result.available ? "bg-card" : "cursor-not-allowed opacity-60"
                }`}
              >
                {url ? (
                  <img src={url} alt={label(result.method)} className="h-36 w-full object-contain" />
                ) : (
                  <span className="grid h-36 place-items-center px-3 text-xs text-muted">{result.error || "Not available"}</span>
                )}
                <span className="flex items-center justify-between border-t border-line px-3 py-2 text-xs">
                  <span>{label(result.method)}</span>
                  <span className="text-muted">{result.processing_time_ms == null ? "not run" : `${result.processing_time_ms} ms`}</span>
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function label(method) {
  if (method === "classical") return "Classical CV";
  if (method === "deep_learning") return "Deep Learning";
  if (method === "hybrid") return "Hybrid AI";
  return method;
}

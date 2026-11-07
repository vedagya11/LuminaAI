const LABELS = {
  illumination: "Illumination map",
  denoised: "Denoised image",
  retinex: "Retinex output",
  clahe: "CLAHE output",
  curve_parameters: "Curve parameters",
  classical: "Classical branch",
  deep_learning: "Deep learning branch",
  deep_learning_weight: "Fusion weight",
};

export default function IntermediateGallery({ images, originalUrl, finalUrl }) {
  const frames = [];
  if (originalUrl) frames.push({ key: "original", label: "Original image", src: originalUrl });
  for (const image of images || []) {
    frames.push({
      key: image.name,
      label: LABELS[image.name] || image.name.replaceAll("_", " "),
      src: `data:${image.media_type};base64,${image.image_base64}`,
    });
  }
  if (finalUrl) frames.push({ key: "final", label: "Final enhanced image", src: finalUrl });

  return (
    <section className="mx-auto max-w-6xl px-4 py-8">
      <h2 className="text-base font-medium">Processing</h2>
      <p className="mt-1 text-sm text-muted">
        Stage images are returned by the API for the selected run. Missing stages were not produced.
      </p>
      {frames.length === 0 ? (
        <p className="mt-4 border border-line bg-card px-4 py-8 text-sm text-muted">
          Enable intermediate images, then run a restoration to see illumination, denoise, Retinex, and CLAHE.
        </p>
      ) : (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {frames.map((frame) => (
              <figure key={frame.key} className="border border-line bg-bg">
                <img src={frame.src} alt={frame.label} className="h-52 w-full object-contain" />
                <figcaption className="border-t border-line px-3 py-2 text-xs text-muted">{frame.label}</figcaption>
              </figure>
            ))}
          </div>
          {!images?.length && (
            <p className="mt-3 text-xs text-muted">
              Enable intermediate images before the next run to add the illumination, denoise, Retinex, and CLAHE stages.
            </p>
          )}
        </>
      )}
    </section>
  );
}

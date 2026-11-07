const ITEMS = [
  ["Classical computer vision", "Multi-scale illumination, per-pixel gamma, Retinex detail, CLAHE, bilateral denoise, and gray-world color balance."],
  ["Zero-DCE++ deep learning", "The published Epoch99 checkpoint estimates enhancement curves and applies them on CPU. The card stays unavailable if the weights do not load."],
  ["Adaptive hybrid fusion", "Dark, clean pixels take more of the network output. Noise and existing highlights take more of the classical output. The weights are measured per image."],
  ["Image quality evaluation", "Luminance, contrast, noise, saturation, dimensions, and processing time come from the returned image. PSNR and SSIM require a reference. NIQE is not computed."],
];

export default function Technology() {
  return (
    <section id="technology" className="mx-auto max-w-6xl px-4 py-8">
      <h2 className="text-base font-medium">Technology</h2>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {ITEMS.map(([title, copy]) => (
          <article key={title} className="border border-line bg-card p-4 shadow-card">
            <h3 className="text-sm font-medium">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-muted">{copy}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export default function Hero() {
  return (
    <section className="mx-auto max-w-6xl px-4 pb-6 pt-14 sm:pt-16">
      <p className="text-xs font-medium tracking-[0.16em] text-muted">AI-POWERED IMAGE RESTORATION</p>
      <h1 className="mt-3 max-w-xl text-3xl font-medium tracking-tight text-ink sm:text-4xl">
        Bring Darkness to Light.
      </h1>
      <p className="mt-3 max-w-xl text-sm leading-6 text-muted sm:text-base">
        Restore details, recover natural illumination and enhance low-light photographs using classical computer vision and deep learning.
      </p>
      <div className="mt-6 flex flex-wrap items-center gap-4">
        <a href="#studio" className="rounded-md bg-accent px-3.5 py-2 text-sm font-medium text-white shadow-card">
          Open Enhancement Studio
        </a>
        <p className="text-sm text-muted">Classical CV | Deep Learning | Hybrid AI</p>
      </div>
    </section>
  );
}

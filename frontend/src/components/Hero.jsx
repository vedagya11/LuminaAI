export default function Hero() {
  return (
    <section className="mx-auto max-w-6xl px-4 pb-8 pt-16 sm:pt-24">
      <p className="rise text-sm uppercase tracking-[0.22em] text-sky-300">Computer vision · P1</p>
      <h1 className="rise delay-1 mt-4 max-w-4xl text-5xl font-semibold leading-[1.05] tracking-tight sm:text-7xl">
        Bring Darkness to{" "}
        <span className="bg-gradient-to-r from-violet-300 via-fuchsia-200 to-sky-300 bg-clip-text text-transparent">
          Light.
        </span>
      </h1>
      <p className="rise delay-2 mt-5 max-w-2xl text-lg text-mist sm:text-xl">
        Intelligent AI-powered low-light image restoration.
      </p>
      <div className="mt-8 flex flex-wrap gap-3">
        <a
          href="#studio"
          className="rounded-full bg-gradient-to-r from-violet-500 to-sky-500 px-5 py-2.5 text-sm font-semibold text-white shadow-glow"
        >
          Enhance an image
        </a>
        <a
          href="#pipeline"
          className="rounded-full border border-white/15 px-5 py-2.5 text-sm text-mist hover:border-white/30 hover:text-white"
        >
          How restoration works
        </a>
      </div>
    </section>
  );
}

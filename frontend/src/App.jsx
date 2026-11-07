import { useEffect, useMemo, useRef, useState } from "react";
import { downloadEncodedImage, enhanceImage, getHealth, getInfo, uploadImage } from "./api/client";
import Comparison from "./components/Comparison";
import Footer from "./components/Footer";
import Hero from "./components/Hero";
import ModeSelect from "./components/ModeSelect";
import Navbar from "./components/Navbar";
import StatsPanel from "./components/StatsPanel";
import Uploader from "./components/Uploader";

const EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"];

export default function App() {
  const inputRef = useRef(null);
  const [health, setHealth] = useState(null);
  const [info, setInfo] = useState(null);
  const [method, setMethod] = useState("");
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [uploadMeta, setUploadMeta] = useState(null);
  const [result, setResult] = useState(null);
  const [phase, setPhase] = useState("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    Promise.all([getHealth(), getInfo()])
      .then(([nextHealth, nextInfo]) => {
        if (cancelled) return;
        setHealth(nextHealth);
        setInfo(nextInfo);
        const available = nextInfo.methods.find((item) => item.available);
        setMethod(available ? available.id : "");
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const afterUrl = useMemo(() => {
    if (!result?.image_base64) return "";
    return `data:${result.media_type};base64,${result.image_base64}`;
  }, [result]);

  const selectedMethod = info?.methods?.find((item) => item.id === method);
  const busy = phase !== "idle";

  function localProblem(next) {
    const extension = next.name.includes(".") ? next.name.slice(next.name.lastIndexOf(".")).toLowerCase() : "";
    if (!EXTENSIONS.includes(extension)) {
      return "Upload a JPG, JPEG, PNG, or WEBP image.";
    }
    if (!next.size) {
      return "The selected file is empty.";
    }
    if (info?.max_upload_bytes && next.size > info.max_upload_bytes) {
      return `File exceeds the ${info.max_upload_bytes} byte upload limit.`;
    }
    return "";
  }

  async function onFile(next) {
    const problem = localProblem(next);
    setResult(null);
    setUploadMeta(null);
    if (problem) {
      setFile(null);
      setPreviewUrl("");
      setError(problem);
      return;
    }
    setFile(next);
    setPreviewUrl(URL.createObjectURL(next));
    setError("");
    setPhase("uploading");
    try {
      const meta = await uploadImage(next);
      setUploadMeta(meta);
    } catch (err) {
      setFile(null);
      setPreviewUrl("");
      setError(err.message);
    } finally {
      setPhase("idle");
    }
  }

  function onClear() {
    setFile(null);
    setPreviewUrl("");
    setUploadMeta(null);
    setResult(null);
    setError("");
  }

  async function onEnhance() {
    if (!file || !selectedMethod?.available) return;
    setError("");
    setPhase("enhancing");
    try {
      const enhanced = await enhanceImage(file, selectedMethod.id);
      setResult(enhanced);
    } catch (err) {
      setResult(null);
      setError(err.message);
    } finally {
      setPhase("idle");
    }
  }

  function onDownload() {
    if (!result) return;
    const stem = (file?.name || "lumina").replace(/\.[^.]+$/, "");
    downloadEncodedImage({
      imageBase64: result.image_base64,
      mediaType: result.media_type,
      filename: `${stem}-lumina.jpg`,
    });
  }

  return (
    <div id="top" className="min-h-screen">
      <Navbar health={health} />
      <main>
        <Hero />
        <section id="studio" className="mx-auto max-w-6xl px-4 pb-8">
          <Uploader
            inputRef={inputRef}
            previewUrl={previewUrl}
            file={file}
            uploadMeta={uploadMeta}
            phase={phase}
            onFile={onFile}
            onClear={onClear}
          />
          <ModeSelect
            methods={info?.methods}
            method={method}
            onChange={(next) => {
              setMethod(next);
              setResult(null);
            }}
            disabled={busy}
          />
          {error && (
            <p role="alert" className="mt-4 rounded-2xl border border-rose-300/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
              {error}
            </p>
          )}
          <div className="mt-5 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={onEnhance}
              disabled={!uploadMeta || !selectedMethod?.available || busy}
              className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-violet-500 to-sky-500 px-5 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              {phase === "enhancing" && <span className="spin inline-block h-3.5 w-3.5 rounded-full border-2 border-white/40 border-t-white" />}
              {phase === "enhancing" ? "Enhancing" : phase === "uploading" ? "Validating" : "Enhance image"}
            </button>
            <button
              type="button"
              onClick={onDownload}
              disabled={!result || busy}
              className="rounded-full border border-white/15 px-5 py-2.5 text-sm disabled:cursor-not-allowed disabled:opacity-40"
            >
              Download enhanced image
            </button>
          </div>
          {result && previewUrl && <Comparison beforeUrl={previewUrl} afterUrl={afterUrl} />}
          <div className="mt-6">
            <StatsPanel result={result} />
          </div>
        </section>
        <section id="pipeline" className="mx-auto grid max-w-6xl gap-4 px-4 py-8 md:grid-cols-3">
          {[
            ["1 · Denoise", "Laplacian noise estimate, then a bilateral filter only when the photograph is actually noisy."],
            ["2 · Retinex", "Multi-scale bright-channel illumination is lifted with an adaptive gamma. Reflectance stays separate from brightness."],
            ["3 · Contrast and color", "CLAHE and a luminance unsharp mask restore local detail. Gray-world gains are clamped, and highlights already near white are protected."],
          ].map(([title, copy]) => (
            <article key={title} className="rounded-3xl border border-white/10 bg-charcoal/70 p-5">
              <h2 className="font-semibold">{title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-mist">{copy}</p>
            </article>
          ))}
        </section>
      </main>
      <Footer />
    </div>
  );
}

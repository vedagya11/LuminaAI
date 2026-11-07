import { useEffect, useMemo, useRef, useState } from "react";
import { compareImages, downloadEncodedImage, enhanceImage, getHealth, getInfo, uploadImage } from "./api/client";
import Comparison from "./components/Comparison";
import Footer from "./components/Footer";
import Hero from "./components/Hero";
import IntermediateGallery from "./components/IntermediateGallery";
import ModeSelect from "./components/ModeSelect";
import Navbar from "./components/Navbar";
import ResultGrid from "./components/ResultGrid";
import StatsPanel from "./components/StatsPanel";
import Technology from "./components/Technology";
import Uploader from "./components/Uploader";

const EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"];

export default function App() {
  const inputRef = useRef(null);
  const [health, setHealth] = useState(null);
  const [info, setInfo] = useState(null);
  const [method, setMethod] = useState("");
  const [file, setFile] = useState(null);
  const [reference, setReference] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [uploadMeta, setUploadMeta] = useState(null);
  const [results, setResults] = useState([]);
  const [originalMetrics, setOriginalMetrics] = useState(null);
  const [selected, setSelected] = useState("");
  const [phase, setPhase] = useState("idle");
  const [error, setError] = useState("");
  const [includeIntermediates, setIncludeIntermediates] = useState(false);
  const [view, setView] = useState("slider");

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

  const selectedResult = results.find((item) => item.method === selected && item.available);
  const afterUrl = useMemo(() => {
    if (!selectedResult?.image_base64) return "";
    return `data:${selectedResult.media_type};base64,${selectedResult.image_base64}`;
  }, [selectedResult]);
  const selectedMethod = info?.methods?.find((item) => item.id === method);
  const busy = phase !== "idle";

  function localProblem(next) {
    const extension = next.name.includes(".") ? next.name.slice(next.name.lastIndexOf(".")).toLowerCase() : "";
    if (!EXTENSIONS.includes(extension)) return "Upload a JPG, JPEG, PNG, or WEBP image.";
    if (!next.size) return "The selected file is empty.";
    if (info?.max_upload_bytes && next.size > info.max_upload_bytes) {
      return `File exceeds the ${info.max_upload_bytes} byte upload limit.`;
    }
    return "";
  }

  async function onFile(next) {
    const problem = localProblem(next);
    setResults([]);
    setOriginalMetrics(null);
    setSelected("");
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
      setUploadMeta(await uploadImage(next));
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
    setResults([]);
    setOriginalMetrics(null);
    setSelected("");
    setReference(null);
    setError("");
  }

  async function onEnhance() {
    if (!file || !selectedMethod?.available) return;
    setError("");
    setPhase("enhancing");
    try {
      const enhanced = await enhanceImage(file, selectedMethod.id, { includeIntermediates, reference });
      setResults((current) => {
        const next = current.filter((item) => item.method !== enhanced.method);
        return [...next, enhanced];
      });
      setSelected(enhanced.method);
      setView("slider");
    } catch (err) {
      setError(err.message);
    } finally {
      setPhase("idle");
    }
  }

  async function onCompare() {
    if (!file) return;
    setError("");
    setPhase("comparing");
    try {
      const compared = await compareImages(file, { includeIntermediates, reference });
      setResults(compared.results);
      setOriginalMetrics(compared.original_no_reference);
      const first = compared.results.find((item) => item.available);
      setSelected(first ? first.method : "");
      setView("grid");
    } catch (err) {
      setError(err.message);
    } finally {
      setPhase("idle");
    }
  }

  function onDownload() {
    if (!selectedResult) return;
    const stem = (file?.name || "lumina").replace(/\.[^.]+$/, "");
    downloadEncodedImage({
      imageBase64: selectedResult.image_base64,
      mediaType: selectedResult.media_type,
      filename: `${stem}-${selectedResult.method}.jpg`,
    });
  }

  const statusText = phase === "enhancing"
    ? "Enhancing"
    : phase === "comparing"
      ? "Comparing methods"
      : phase === "uploading"
        ? "Validating"
        : "Enhance";

  return (
    <div id="top" className="min-h-screen bg-bg">
      <Navbar health={health} />
      <main>
        <Hero />
        <section id="studio" className="mx-auto max-w-6xl px-4 py-8">
          <h2 className="text-base font-medium">Enhancement studio</h2>
          <div className="mt-4 grid items-start gap-4 lg:grid-cols-2">
            <Uploader
              inputRef={inputRef}
              previewUrl={previewUrl}
              file={file}
              uploadMeta={uploadMeta}
              phase={phase}
              maxBytes={info?.max_upload_bytes}
              onFile={onFile}
              onClear={onClear}
            />
            <div className="rounded-md border border-line bg-panel p-4 shadow-card">
              <ModeSelect methods={info?.methods} method={method} onChange={setMethod} disabled={busy} />
              <div className="mt-4 grid gap-3">
                <label className="text-xs text-muted">
                  Optional reference for PSNR and SSIM
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
                    className="mt-1 block w-full text-xs text-ink"
                    onChange={(event) => setReference(event.target.files?.[0] || null)}
                  />
                </label>
                <label className="flex items-start gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={includeIntermediates}
                    onChange={(event) => setIncludeIntermediates(event.target.checked)}
                    className="mt-1"
                  />
                  <span>
                    <span className="block text-ink">Include intermediate images</span>
                    <span className="mt-0.5 block text-xs text-muted">Illumination, denoise, Retinex, CLAHE, and curve maps from the stages that run.</span>
                  </span>
                </label>
              </div>
              {error && (
                <p role="alert" className="mt-4 border border-danger/40 bg-card px-3 py-2 text-sm text-danger">
                  {error}
                </p>
              )}
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={onEnhance}
                  disabled={!uploadMeta || !selectedMethod?.available || busy}
                  className="inline-flex items-center gap-2 rounded-md bg-accent px-3 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {busy && <span className="spin inline-block h-3 w-3 rounded-full border-2 border-white/30 border-t-white" />}
                  {statusText}
                </button>
                <button
                  type="button"
                  onClick={onCompare}
                  disabled={!uploadMeta || busy}
                  className="rounded-md border border-line bg-card px-3 py-2 text-sm text-ink disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Compare available methods
                </button>
              </div>
            </div>
          </div>
        </section>
        <section id="comparison" className="mx-auto max-w-6xl px-4 py-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-base font-medium">Comparison</h2>
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={() => setView("slider")} className={viewButton(view === "slider")}>Before and after</button>
              <button type="button" onClick={() => setView("grid")} className={viewButton(view === "grid")}>Side by side</button>
              <button
                type="button"
                onClick={onDownload}
                disabled={!selectedResult || busy}
                className="rounded-md border border-line bg-card px-3 py-1.5 text-sm disabled:cursor-not-allowed disabled:opacity-40"
              >
                Download
              </button>
            </div>
          </div>
          {results.filter((item) => item.available).length > 1 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {results.filter((item) => item.available).map((item) => (
                <button key={item.method} type="button" onClick={() => setSelected(item.method)} className={viewButton(selected === item.method)}>
                  {item.method.replaceAll("_", " ")} · {item.processing_time_ms} ms
                </button>
              ))}
            </div>
          )}
          <div className="mt-4">
            {view === "slider" && selectedResult && previewUrl && afterUrl && (
              <Comparison beforeUrl={previewUrl} afterUrl={afterUrl} />
            )}
            {view === "grid" && previewUrl && results.length > 0 && (
              <ResultGrid originalUrl={previewUrl} results={results} selected={selected} onSelect={setSelected} />
            )}
            {!(selectedResult && previewUrl) && (
              <p className="border border-line bg-card px-4 py-16 text-center text-sm text-muted">
                The original and enhanced images appear here after a restoration.
              </p>
            )}
          </div>
        </section>
        <StatsPanel result={selectedResult} original={originalMetrics} />
        <IntermediateGallery images={selectedResult?.intermediates} originalUrl={previewUrl} finalUrl={afterUrl} />
        <Technology />
      </main>
      <Footer />
    </div>
  );
}

function viewButton(active) {
  return `rounded-md px-3 py-1.5 text-sm ${active ? "bg-accent text-white" : "border border-line bg-card text-muted"}`;
}

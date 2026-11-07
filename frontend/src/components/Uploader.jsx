export default function Uploader({
  inputRef,
  previewUrl,
  file,
  uploadMeta,
  phase,
  onFile,
  onClear,
}) {
  function assign(next) {
    if (next) onFile(next);
  }

  return (
    <div className="rounded-3xl border border-white/10 bg-charcoal/80 p-4 shadow-glow sm:p-6">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">Upload</h2>
        <p className="text-xs uppercase tracking-wider text-mist">JPG · JPEG · PNG · WEBP</p>
      </div>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          assign(event.dataTransfer.files?.[0]);
        }}
        className="flex min-h-48 w-full flex-col items-center justify-center rounded-2xl border border-dashed border-violet-300/30 bg-navy/70 px-6 py-8 text-center transition hover:border-sky-300/50"
      >
        {previewUrl ? (
          <img src={previewUrl} alt="Selected upload preview" className="max-h-64 rounded-xl object-contain" />
        ) : (
          <>
            <span className="text-base text-white">Drop a dark photograph here</span>
            <span className="mt-2 text-sm text-mist">or click to browse. The file is validated by the API before enhancement.</span>
          </>
        )}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
        className="hidden"
        onChange={(event) => {
          assign(event.target.files?.[0]);
          event.target.value = "";
        }}
      />
      {file && (
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-mist">
          <p>
            {file.name}
            {uploadMeta
              ? ` · ${uploadMeta.width}×${uploadMeta.height} · ${formatBytes(uploadMeta.size_bytes)} · ${uploadMeta.format}`
              : phase === "uploading"
                ? " · validating…"
                : ""}
          </p>
          <button type="button" onClick={onClear} className="text-sky-300 hover:text-white">
            Remove
          </button>
        </div>
      )}
    </div>
  );
}

function formatBytes(size) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

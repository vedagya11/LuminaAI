import { ImageUp } from "lucide-react";

export default function Uploader({
  inputRef,
  previewUrl,
  file,
  uploadMeta,
  phase,
  maxBytes,
  onFile,
  onClear,
}) {
  function assign(next) {
    if (next) onFile(next);
  }

  return (
    <div className="rounded-md border border-line bg-card p-4 shadow-card">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-sm font-medium">Original</h2>
        <p className="text-xs text-muted">JPG, JPEG, PNG, WEBP</p>
      </div>
      <div
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          assign(event.dataTransfer.files?.[0]);
        }}
        className="mt-3 flex min-h-44 flex-col items-center justify-center border border-dashed border-line bg-panel px-4 py-6 text-center"
      >
        <ImageUp size={18} strokeWidth={1.75} className="text-muted" aria-hidden="true" />
        <p className="mt-3 text-sm text-ink">Drop a photograph here</p>
        <p className="mt-1 text-xs text-muted">Maximum size {maxBytes ? formatBytes(maxBytes) : "reported by the API"}</p>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="mt-4 rounded-md border border-line bg-card px-3 py-1.5 text-sm text-ink hover:border-accent"
        >
          Browse files
        </button>
      </div>
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
      <div className="mt-3 border border-line bg-bg">
        {previewUrl ? (
          <img src={previewUrl} alt="Original upload preview" className="max-h-80 w-full object-contain" />
        ) : (
          <p className="px-4 py-10 text-center text-sm text-muted">Original preview appears after a valid upload.</p>
        )}
      </div>
      {file && (
        <div className="mt-3 flex items-center justify-between gap-3 text-xs text-muted">
          <p className="truncate">
            {file.name}
            {uploadMeta
              ? ` · ${uploadMeta.width}×${uploadMeta.height} · ${formatBytes(uploadMeta.size_bytes)}`
              : phase === "uploading"
                ? " · validating"
                : ""}
          </p>
          <button type="button" onClick={onClear} className="shrink-0 text-ink hover:text-accent">
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

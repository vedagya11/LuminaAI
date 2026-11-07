const SHORT = {
  classical: "Retinex, adaptive gamma, CLAHE, and edge-preserving denoise.",
  deep_learning: "Zero-DCE++ pretrained curves, inferred on CPU.",
  hybrid: "Spatial fusion of the classical result and the network result.",
};

export default function ModeSelect({ methods, method, onChange, disabled }) {
  const items = methods?.length
    ? methods
    : [
        {
          id: "classical",
          name: "Classical CV",
          available: false,
          description: "Waiting for the API to report which methods are available.",
        },
      ];

  return (
    <fieldset disabled={disabled}>
      <legend className="text-sm font-medium">Enhancement mode</legend>
      <div className="mt-3 grid gap-2">
        {items.map((item) => {
          const selected = item.available && item.id === method;
          return (
            <label
              key={item.id}
              className={`block border px-3 py-3 text-left ${
                item.available ? "cursor-pointer" : "cursor-not-allowed opacity-60"
              } ${selected ? "border-accent bg-panel" : "border-line bg-card"}`}
            >
              <input
                type="radio"
                name="method"
                className="sr-only"
                value={item.id}
                checked={selected}
                disabled={!item.available || disabled}
                onChange={() => onChange(item.id)}
              />
              <span className="flex items-center justify-between gap-3">
                <span className="text-sm font-medium">{item.name}</span>
                <span className={`text-xs ${item.available ? "text-success" : "text-muted"}`}>
                  {selected ? "Selected" : item.available ? "Available" : "Unavailable"}
                </span>
              </span>
              <span className="mt-1 block text-xs leading-5 text-muted">
                {item.available ? SHORT[item.id] || item.description : item.description}
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

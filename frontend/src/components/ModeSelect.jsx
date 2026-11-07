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
    <fieldset className="mt-6" disabled={disabled}>
      <legend className="mb-3 text-lg font-semibold">Enhancement mode</legend>
      <div className="grid gap-3 md:grid-cols-3">
        {items.map((item) => {
          const selected = item.available && item.id === method;
          return (
            <label
              key={item.id}
              className={`rounded-2xl border p-4 text-left ${
                item.available ? "cursor-pointer" : "cursor-not-allowed opacity-70"
              } ${
                selected
                  ? "border-violet-300/70 bg-violet-500/15"
                  : "border-white/10 bg-navy/60"
              }`}
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
              <span className="flex items-center justify-between gap-2">
                <span className="font-medium">{item.name}</span>
                <span className={`text-xs ${item.available ? "text-emerald-300" : "text-amber-200"}`}>
                  {item.available ? "Ready" : "Not integrated"}
                </span>
              </span>
              <span className="mt-2 block text-sm leading-relaxed text-mist">{item.description}</span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

"use client";

interface Props {
  label: string;
  items: string[];
  onChange: (items: string[]) => void;
  placeholder?: string;
}

export default function MarketBulletEditor({ label, items, onChange, placeholder }: Props) {
  function handleChange(index: number, value: string) {
    const updated = [...items];
    updated[index] = value;
    onChange(updated);
  }

  function handleRemove(index: number) {
    onChange(items.filter((_, i) => i !== index));
  }

  function handleAdd() {
    onChange([...items, ""]);
  }

  function handleKeyDown(e: React.KeyboardEvent, index: number) {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAdd();
    }
    if (e.key === "Backspace" && items[index] === "" && items.length > 0) {
      e.preventDefault();
      handleRemove(index);
    }
  }

  return (
    <div>
      <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
      <div className="space-y-1">
        {items.map((item, i) => (
          <div key={i} className="flex items-start gap-1.5">
            <span className="text-gray-300 text-xs mt-2 select-none">&#8226;</span>
            <input
              type="text"
              value={item}
              onChange={(e) => handleChange(i, e.target.value)}
              onKeyDown={(e) => handleKeyDown(e, i)}
              className="flex-1 px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30 focus:border-cc-mid"
            />
            <button
              onClick={() => handleRemove(i)}
              aria-label="Remove item"
              className="text-gray-300 hover:text-red-400 mt-1 p-0.5 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        ))}
      </div>
      <button
        onClick={handleAdd}
        className="mt-1.5 text-xs text-cc-mid hover:text-cc-dark transition-colors flex items-center gap-1"
      >
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        {placeholder || "Add item"}
      </button>
    </div>
  );
}

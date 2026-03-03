"use client";

import SectionCard from "./SectionCard";

interface Props {
  title: string;
  items: string[];
  onChange: (items: string[]) => void;
}

export default function BulletEditor({ title, items, onChange }: Props) {
  const updateItem = (index: number, value: string) => {
    const updated = [...items];
    updated[index] = value;
    onChange(updated);
  };

  const addItem = () => {
    onChange([...items, ""]);
  };

  const removeItem = (index: number) => {
    onChange(items.filter((_, i) => i !== index));
  };

  const moveUp = (index: number) => {
    if (index === 0) return;
    const updated = [...items];
    [updated[index - 1], updated[index]] = [updated[index], updated[index - 1]];
    onChange(updated);
  };

  const moveDown = (index: number) => {
    if (index === items.length - 1) return;
    const updated = [...items];
    [updated[index], updated[index + 1]] = [updated[index + 1], updated[index]];
    onChange(updated);
  };

  return (
    <SectionCard title={title}>
      <div className="space-y-1.5">
        {items.map((item, i) => (
          <div key={i} className="flex gap-1 items-start group">
            <span className="text-gray-400 text-xs mt-2 w-4">{i + 1}.</span>
            <textarea
              value={item}
              onChange={(e) => updateItem(i, e.target.value)}
              rows={1}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm resize-none
                         focus:ring-2 focus:ring-cc-mid focus:border-cc-mid"
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = "auto";
                target.style.height = target.scrollHeight + "px";
              }}
            />
            <div className="flex flex-col opacity-0 group-hover:opacity-100 transition-opacity">
              <button onClick={() => moveUp(i)} className="text-gray-400 hover:text-cc-mid text-xs leading-none">
                ^
              </button>
              <button onClick={() => moveDown(i)} className="text-gray-400 hover:text-cc-mid text-xs leading-none">
                v
              </button>
            </div>
            <button
              onClick={() => removeItem(i)}
              className="text-red-300 hover:text-red-500 text-sm mt-1 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              x
            </button>
          </div>
        ))}
      </div>
      <button
        onClick={addItem}
        className="text-xs text-cc-mid hover:underline mt-2"
      >
        + Add bullet point
      </button>
    </SectionCard>
  );
}

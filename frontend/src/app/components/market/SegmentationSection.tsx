"use client";

import { MarketSegment } from "@/lib/types";
import MarketSectionCard from "./MarketSectionCard";

interface Props {
  segments: MarketSegment[];
  onChange: (data: MarketSegment[]) => void;
}

const emptySegment: MarketSegment = { name: "", size: "", share_pct: null, growth_rate: "", description: "" };

export default function SegmentationSection({ segments: data, onChange }: Props) {
  const update = (idx: number, patch: Partial<MarketSegment>) => {
    const next = data.map((s, i) => (i === idx ? { ...s, ...patch } : s));
    onChange(next);
  };
  const remove = (idx: number) => onChange(data.filter((_, i) => i !== idx));
  const add = () => onChange([...data, { ...emptySegment }]);

  return (
    <MarketSectionCard title="Market Segmentation" slideNumber={3}>
      <div className="space-y-3">
        {data.map((seg, idx) => (
          <div key={idx} className="border border-gray-200 rounded p-2 space-y-2">
            <div className="flex items-center gap-2">
              <input type="text" value={seg.name} onChange={(e) => update(idx, { name: e.target.value })}
                placeholder="Segment name" className="flex-1 px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
              <button onClick={() => remove(idx)} aria-label="Remove segment" className="text-red-400 hover:text-red-600 text-xs">✕</button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <input type="text" value={seg.size} onChange={(e) => update(idx, { size: e.target.value })}
                placeholder="Size (e.g. EUR 1.2bn)" className="px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
              <input type="text"
                value={seg.share_pct !== null ? `${seg.share_pct}%` : ""}
                onChange={(e) => {
                  const val = e.target.value.replace("%", "");
                  const num = parseFloat(val);
                  update(idx, { share_pct: isNaN(num) ? null : num });
                }}
                placeholder="Share %" className="px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
              <input type="text" value={seg.growth_rate} onChange={(e) => update(idx, { growth_rate: e.target.value })}
                placeholder="Growth rate" className="px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
            </div>
            <textarea value={seg.description} onChange={(e) => update(idx, { description: e.target.value })}
              placeholder="Description..." rows={2}
              className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
          </div>
        ))}
      </div>
      <button onClick={add} className="text-xs text-cc-mid hover:underline mt-1">+ Add segment</button>
    </MarketSectionCard>
  );
}

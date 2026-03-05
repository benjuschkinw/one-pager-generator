"use client";

import { ValueChain, ValueChainStage } from "@/lib/types";
import MarketSectionCard from "./MarketSectionCard";
import MarketBulletEditor from "./MarketBulletEditor";

interface Props {
  data: ValueChain;
  onChange: (data: ValueChain) => void;
}

const emptyStage: ValueChainStage = { name: "", description: "", typical_margin: "" };

export default function ValueChainSection({ data, onChange }: Props) {
  const updateStage = (idx: number, patch: Partial<ValueChainStage>) => {
    const next = data.stages.map((s, i) => (i === idx ? { ...s, ...patch } : s));
    onChange({ ...data, stages: next });
  };
  const removeStage = (idx: number) => onChange({ ...data, stages: data.stages.filter((_, i) => i !== idx) });
  const addStage = () => onChange({ ...data, stages: [...data.stages, { ...emptyStage }] });

  return (
    <MarketSectionCard title="Value Chain" slideNumber={8}>
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-2">Stages</label>
        <div className="space-y-2">
          {data.stages.map((stage, idx) => (
            <div key={idx} className="border border-gray-200 rounded p-2 space-y-2">
              <div className="flex items-center gap-2">
                <input type="text" value={stage.name} onChange={(e) => updateStage(idx, { name: e.target.value })}
                  placeholder="Stage name" className="flex-1 px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
                <input type="text" value={stage.typical_margin} onChange={(e) => updateStage(idx, { typical_margin: e.target.value })}
                  placeholder="Margin" className="w-24 px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
                <button onClick={() => removeStage(idx)} className="text-red-400 hover:text-red-600 text-xs">✕</button>
              </div>
              <textarea value={stage.description} onChange={(e) => updateStage(idx, { description: e.target.value })}
                placeholder="Description..." rows={2}
                className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
            </div>
          ))}
        </div>
        <button onClick={addStage} className="text-xs text-cc-primary hover:underline mt-1">+ Add stage</button>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Margin Distribution</label>
        <textarea value={data.margin_distribution} onChange={(e) => onChange({ ...data, margin_distribution: e.target.value })}
          rows={2} className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
      </div>

      <MarketBulletEditor label="Dominant Business Models" items={data.dominant_business_models}
        onChange={(dominant_business_models) => onChange({ ...data, dominant_business_models })} placeholder="Add model..." />
    </MarketSectionCard>
  );
}

"use client";

import { StrategicImplications, StrategicRecommendation } from "@/lib/types";
import MarketSectionCard from "./MarketSectionCard";
import MarketBulletEditor from "./MarketBulletEditor";

interface Props {
  data: StrategicImplications;
  onChange: (data: StrategicImplications) => void;
}

const emptyRec: StrategicRecommendation = { title: "", description: "", risk_benefit: "" };

export default function StrategicImplicationsSection({ data, onChange }: Props) {
  const updateRec = (idx: number, patch: Partial<StrategicRecommendation>) => {
    const next = data.recommendations.map((r, i) => (i === idx ? { ...r, ...patch } : r));
    onChange({ ...data, recommendations: next });
  };
  const removeRec = (idx: number) => onChange({ ...data, recommendations: data.recommendations.filter((_, i) => i !== idx) });
  const addRec = () => onChange({ ...data, recommendations: [...data.recommendations, { ...emptyRec }] });

  return (
    <MarketSectionCard title="Strategic Implications" slideNumber={10}>
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Investment Attractiveness</label>
        <textarea value={data.investment_attractiveness} onChange={(e) => onChange({ ...data, investment_attractiveness: e.target.value })}
          rows={2} className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
      </div>

      <MarketBulletEditor label="Key Risks" items={data.key_risks}
        onChange={(key_risks) => onChange({ ...data, key_risks })} placeholder="Add risk..." />

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-2">Recommendations</label>
        <div className="space-y-3">
          {data.recommendations.map((rec, idx) => (
            <div key={idx} className="border border-gray-200 rounded p-2 space-y-2">
              <div className="flex items-center gap-2">
                <input type="text" value={rec.title} onChange={(e) => updateRec(idx, { title: e.target.value })}
                  placeholder="Recommendation title" className="flex-1 px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
                <button onClick={() => removeRec(idx)} className="text-red-400 hover:text-red-600 text-xs">✕</button>
              </div>
              <textarea value={rec.description} onChange={(e) => updateRec(idx, { description: e.target.value })}
                placeholder="Description..." rows={2}
                className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
              <textarea value={rec.risk_benefit} onChange={(e) => updateRec(idx, { risk_benefit: e.target.value })}
                placeholder="Risk / Benefit..." rows={1}
                className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
            </div>
          ))}
        </div>
        <button onClick={addRec} className="text-xs text-cc-primary hover:underline mt-1">+ Add recommendation</button>
      </div>
    </MarketSectionCard>
  );
}

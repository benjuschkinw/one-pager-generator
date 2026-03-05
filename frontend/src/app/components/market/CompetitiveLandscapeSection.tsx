"use client";

import { CompetitiveLandscape, CompetitorProfile } from "@/lib/types";
import MarketSectionCard from "./MarketSectionCard";
import MarketBulletEditor from "./MarketBulletEditor";

interface Props {
  data: CompetitiveLandscape;
  onChange: (data: CompetitiveLandscape) => void;
}

const emptyCompetitor: CompetitorProfile = { name: "", market_share: "", revenue: "", hq: "", strengths: [] };

export default function CompetitiveLandscapeSection({ data, onChange }: Props) {
  const updatePlayer = (idx: number, patch: Partial<CompetitorProfile>) => {
    const next = data.top_players.map((p, i) => (i === idx ? { ...p, ...patch } : p));
    onChange({ ...data, top_players: next });
  };
  const removePlayer = (idx: number) => onChange({ ...data, top_players: data.top_players.filter((_, i) => i !== idx) });
  const addPlayer = () => onChange({ ...data, top_players: [...data.top_players, { ...emptyCompetitor }] });

  return (
    <MarketSectionCard title="Competitive Landscape" slideNumber={4}>
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Fragmentation</label>
          <select value={data.fragmentation} onChange={(e) => onChange({ ...data, fragmentation: e.target.value })}
            className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30">
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">HHI Index</label>
          <input type="text"
            value={data.hhi_index !== null ? String(data.hhi_index) : ""}
            onChange={(e) => { const n = parseFloat(e.target.value); onChange({ ...data, hhi_index: isNaN(n) ? null : n }); }}
            placeholder="e.g. 850" className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Avg. Revenue</label>
          <input type="text" value={data.avg_company_revenue} onChange={(e) => onChange({ ...data, avg_company_revenue: e.target.value })}
            placeholder="EUR Xm" className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
        </div>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Consolidation Trend</label>
        <textarea value={data.consolidation_trend} onChange={(e) => onChange({ ...data, consolidation_trend: e.target.value })}
          rows={2} className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-2">Top Players</label>
        <div className="space-y-3">
          {data.top_players.map((p, idx) => (
            <div key={idx} className="border border-gray-200 rounded p-2 space-y-2">
              <div className="flex items-center gap-2">
                <input type="text" value={p.name} onChange={(e) => updatePlayer(idx, { name: e.target.value })}
                  placeholder="Company name" className="flex-1 px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
                <button onClick={() => removePlayer(idx)} aria-label="Remove competitor" className="text-red-400 hover:text-red-600 text-xs">✕</button>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <input type="text" value={p.market_share} onChange={(e) => updatePlayer(idx, { market_share: e.target.value })}
                  placeholder="Market share" className="px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
                <input type="text" value={p.revenue} onChange={(e) => updatePlayer(idx, { revenue: e.target.value })}
                  placeholder="Revenue" className="px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
                <input type="text" value={p.hq} onChange={(e) => updatePlayer(idx, { hq: e.target.value })}
                  placeholder="HQ" className="px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
              </div>
              <MarketBulletEditor label="Strengths" items={p.strengths}
                onChange={(strengths) => updatePlayer(idx, { strengths })} placeholder="Add strength..." />
            </div>
          ))}
        </div>
        <button onClick={addPlayer} className="text-xs text-cc-primary hover:underline mt-1">+ Add competitor</button>
      </div>
    </MarketSectionCard>
  );
}

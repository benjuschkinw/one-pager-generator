"use client";

import { BuyAndBuild } from "@/lib/types";
import MarketSectionCard from "./MarketSectionCard";
import MarketBulletEditor from "./MarketBulletEditor";

interface Props {
  data: BuyAndBuild;
  onChange: (data: BuyAndBuild) => void;
}

export default function BuyAndBuildSection({ data, onChange }: Props) {
  return (
    <MarketSectionCard title="Buy & Build" slideNumber={9}>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Fragmentation Score</label>
          <input type="text"
            value={data.fragmentation_score !== null ? String(data.fragmentation_score) : ""}
            onChange={(e) => { const n = parseFloat(e.target.value); onChange({ ...data, fragmentation_score: isNaN(n) ? null : n }); }}
            placeholder="1-10" className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Est. Targets DACH</label>
          <input type="text" value={data.estimated_targets_dach} onChange={(e) => onChange({ ...data, estimated_targets_dach: e.target.value })}
            placeholder="e.g. 200+" className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Add-on Profile</label>
        <textarea value={data.add_on_profile} onChange={(e) => onChange({ ...data, add_on_profile: e.target.value })}
          rows={2} className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Consolidation Rationale</label>
        <textarea value={data.consolidation_rationale} onChange={(e) => onChange({ ...data, consolidation_rationale: e.target.value })}
          rows={2} className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
      </div>

      <MarketBulletEditor label="Platform Candidates" items={data.platform_candidates}
        onChange={(platform_candidates) => onChange({ ...data, platform_candidates })} placeholder="Add candidate..." />
    </MarketSectionCard>
  );
}

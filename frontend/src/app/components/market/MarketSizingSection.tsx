"use client";

import { MarketSizing } from "@/lib/types";
import MarketSectionCard from "./MarketSectionCard";
import MarketBulletEditor from "./MarketBulletEditor";

interface Props {
  data: MarketSizing;
  onChange: (data: MarketSizing) => void;
}

export default function MarketSizingSection({ data, onChange }: Props) {
  return (
    <MarketSectionCard title="Market Sizing" slideNumber={2}>
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">TAM</label>
          <input type="text" value={data.tam} onChange={(e) => onChange({ ...data, tam: e.target.value })}
            placeholder="EUR X.Xbn" className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">SAM</label>
          <input type="text" value={data.sam} onChange={(e) => onChange({ ...data, sam: e.target.value })}
            placeholder="EUR X.Xm" className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">SOM</label>
          <input type="text" value={data.som} onChange={(e) => onChange({ ...data, som: e.target.value })}
            placeholder="EUR X.Xm" className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
        </div>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">CAGR (%)</label>
          <input type="number" step="0.1"
            value={data.cagr !== null ? (data.cagr * 100).toFixed(1) : ""}
            onChange={(e) => {
              const num = parseFloat(e.target.value);
              onChange({ ...data, cagr: isNaN(num) ? null : num / 100 });
            }}
            placeholder="6.8" className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">CAGR Period</label>
          <input type="text" value={data.cagr_period} onChange={(e) => onChange({ ...data, cagr_period: e.target.value })}
            placeholder="2025-2033" className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Methodology</label>
          <select value={data.methodology} onChange={(e) => onChange({ ...data, methodology: e.target.value })}
            className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30">
            <option value="">--</option>
            <option value="Top-Down">Top-Down</option>
            <option value="Bottom-Up">Bottom-Up</option>
          </select>
        </div>
      </div>
      <MarketBulletEditor label="Assumptions" items={data.assumptions} onChange={(assumptions) => onChange({ ...data, assumptions })} placeholder="Add assumption..." />
    </MarketSectionCard>
  );
}

"use client";

import { ExecutiveSummary } from "@/lib/types";
import MarketSectionCard from "./MarketSectionCard";
import MarketBulletEditor from "./MarketBulletEditor";

interface Props {
  data: ExecutiveSummary;
  onChange: (data: ExecutiveSummary) => void;
}

export default function ExecutiveSummarySection({ data, onChange }: Props) {
  return (
    <MarketSectionCard title="Executive Summary" slideNumber={1}>
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Action Title</label>
        <input
          type="text"
          value={data.title}
          onChange={(e) => onChange({ ...data, title: e.target.value })}
          placeholder="e.g. Dental-Labore: Konsolidierungswelle schafft PE-Chancen"
          className="w-full px-3 py-1.5 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30 focus:border-cc-mid"
        />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Market Verdict</label>
        <textarea
          value={data.market_verdict}
          onChange={(e) => onChange({ ...data, market_verdict: e.target.value })}
          placeholder="Overall assessment (1-2 sentences)"
          rows={2}
          className="w-full px-3 py-1.5 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30 focus:border-cc-mid resize-none"
        />
      </div>
      <MarketBulletEditor
        label="Key Findings"
        items={data.key_findings}
        onChange={(key_findings) => onChange({ ...data, key_findings })}
        placeholder="Add key finding..."
      />
    </MarketSectionCard>
  );
}

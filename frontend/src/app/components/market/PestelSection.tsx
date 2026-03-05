"use client";

import { PestelAnalysis, PestelFactor } from "@/lib/types";
import MarketSectionCard from "./MarketSectionCard";
import MarketBulletEditor from "./MarketBulletEditor";

interface Props {
  data: PestelAnalysis;
  onChange: (data: PestelAnalysis) => void;
}

const DIMENSIONS: { key: keyof PestelAnalysis; label: string }[] = [
  { key: "political", label: "Political" },
  { key: "economic", label: "Economic" },
  { key: "social", label: "Social" },
  { key: "technological", label: "Technological" },
  { key: "environmental", label: "Environmental" },
  { key: "legal", label: "Legal" },
];

const RATINGS = ["positive", "neutral", "negative"];

function PestelDimension({ label, factor, onChange }: { label: string; factor: PestelFactor; onChange: (f: PestelFactor) => void }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-gray-700 w-28">{label}</span>
        <select value={factor.rating} onChange={(e) => onChange({ ...factor, rating: e.target.value })}
          className="px-2 py-0.5 border border-gray-200 rounded text-xs focus:ring-1 focus:ring-cc-mid/30">
          {RATINGS.map((r) => <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>)}
        </select>
      </div>
      <MarketBulletEditor label="" items={factor.points}
        onChange={(points) => onChange({ ...factor, points })} placeholder="Add point..." />
    </div>
  );
}

export default function PestelSection({ data, onChange }: Props) {
  return (
    <MarketSectionCard title="PESTEL Analysis" slideNumber={6}>
      <div className="grid grid-cols-2 gap-4">
        {DIMENSIONS.map(({ key, label }) => (
          <PestelDimension key={key} label={label} factor={data[key]}
            onChange={(f) => onChange({ ...data, [key]: f })} />
        ))}
      </div>
    </MarketSectionCard>
  );
}

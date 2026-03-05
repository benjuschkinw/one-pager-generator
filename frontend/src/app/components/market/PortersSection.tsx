"use client";

import { PortersFiveForces, ForceAssessment } from "@/lib/types";
import MarketSectionCard from "./MarketSectionCard";

interface Props {
  data: PortersFiveForces;
  onChange: (data: PortersFiveForces) => void;
}

const FORCES: { key: keyof PortersFiveForces; label: string }[] = [
  { key: "rivalry", label: "Competitive Rivalry" },
  { key: "buyer_power", label: "Buyer Power" },
  { key: "supplier_power", label: "Supplier Power" },
  { key: "threat_new_entrants", label: "Threat of New Entrants" },
  { key: "threat_substitutes", label: "Threat of Substitutes" },
];

const RATINGS = ["low", "medium", "high"];

function ForceRow({ label, force, onChange }: { label: string; force: ForceAssessment; onChange: (f: ForceAssessment) => void }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-gray-700 w-44">{label}</span>
        <select value={force.rating} onChange={(e) => onChange({ ...force, rating: e.target.value })}
          className="px-2 py-0.5 border border-gray-200 rounded text-xs focus:ring-1 focus:ring-cc-mid/30">
          {RATINGS.map((r) => <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>)}
        </select>
      </div>
      <textarea value={force.explanation} onChange={(e) => onChange({ ...force, explanation: e.target.value })}
        placeholder="Explanation..." rows={2}
        className="w-full px-2 py-1 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid/30" />
    </div>
  );
}

export default function PortersSection({ data, onChange }: Props) {
  return (
    <MarketSectionCard title="Porter's Five Forces" slideNumber={7}>
      <div className="space-y-3">
        {FORCES.map(({ key, label }) => (
          <ForceRow key={key} label={label} force={data[key]}
            onChange={(f) => onChange({ ...data, [key]: f })} />
        ))}
      </div>
    </MarketSectionCard>
  );
}

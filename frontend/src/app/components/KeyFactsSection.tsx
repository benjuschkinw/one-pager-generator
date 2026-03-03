"use client";

import { KeyFacts } from "@/lib/types";
import SectionCard from "./SectionCard";

interface Props {
  data: KeyFacts;
  onChange: (data: KeyFacts) => void;
}

export default function KeyFactsSection({ data, onChange }: Props) {
  const update = (field: keyof KeyFacts, value: string) => {
    onChange({ ...data, [field]: value });
  };

  const updateManagement = (index: number, value: string) => {
    const mgmt = [...data.management];
    mgmt[index] = value;
    onChange({ ...data, management: mgmt });
  };

  const addManagement = () => {
    onChange({ ...data, management: [...data.management, ""] });
  };

  const removeManagement = (index: number) => {
    onChange({ ...data, management: data.management.filter((_, i) => i !== index) });
  };

  return (
    <SectionCard title="Key Facts">
      <div className="space-y-2">
        <Row label="Founded" value={data.founded} onChange={(v) => update("founded", v)} />
        <Row label="HQ" value={data.hq} onChange={(v) => update("hq", v)} />
        <Row label="Website" value={data.website} onChange={(v) => update("website", v)} />
        <Row label="Industry" value={data.industry} onChange={(v) => update("industry", v)} />
        <Row label="Niche" value={data.niche} onChange={(v) => update("niche", v)} />
        <div className="grid grid-cols-2 gap-2">
          <Row label="Revenue" value={data.revenue} onChange={(v) => update("revenue", v)} />
          <Row label="Year" value={data.revenue_year} onChange={(v) => update("revenue_year", v)} />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <Row label="EBITDA" value={data.ebitda} onChange={(v) => update("ebitda", v)} />
          <Row label="Year" value={data.ebitda_year} onChange={(v) => update("ebitda_year", v)} />
        </div>
        <Row label="Employees" value={data.employees} onChange={(v) => update("employees", v)} />

        {/* Management */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Management</label>
          {data.management.map((m, i) => (
            <div key={i} className="flex gap-1 mb-1">
              <input
                type="text"
                value={m}
                onChange={(e) => updateManagement(i, e.target.value)}
                className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-cc-mid focus:border-cc-mid"
              />
              <button
                onClick={() => removeManagement(i)}
                className="text-red-400 hover:text-red-600 px-1"
              >
                x
              </button>
            </div>
          ))}
          <button
            onClick={addManagement}
            className="text-xs text-cc-mid hover:underline mt-1"
          >
            + Add management entry
          </button>
        </div>
      </div>
    </SectionCard>
  );
}

function Row({ label, value, onChange }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-500 mb-0.5">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-cc-mid focus:border-cc-mid"
      />
    </div>
  );
}

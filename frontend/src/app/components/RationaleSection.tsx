"use client";

import { InvestmentRationale } from "@/lib/types";
import SectionCard from "./SectionCard";

interface Props {
  data: InvestmentRationale;
  onChange: (data: InvestmentRationale) => void;
}

export default function RationaleSection({ data, onChange }: Props) {
  const updatePro = (index: number, value: string) => {
    const pros = [...data.pros];
    pros[index] = value;
    onChange({ ...data, pros });
  };

  const updateCon = (index: number, value: string) => {
    const cons = [...data.cons];
    cons[index] = value;
    onChange({ ...data, cons });
  };

  return (
    <SectionCard title="Investment Rationale">
      {/* Pros */}
      <div className="mb-4">
        <h4 className="text-xs font-semibold text-green-700 mb-2 flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
          Pros
        </h4>
        {data.pros.map((pro, i) => (
          <div key={i} className="flex gap-1 mb-1">
            <span className="text-green-500 mt-1">+</span>
            <input
              type="text"
              value={pro}
              onChange={(e) => updatePro(i, e.target.value)}
              className="flex-1 px-2 py-1 border border-green-200 rounded text-sm focus:ring-2 focus:ring-green-400 focus:border-green-400"
            />
            <button
              onClick={() => onChange({ ...data, pros: data.pros.filter((_, j) => j !== i) })}
              className="text-red-300 hover:text-red-500 text-sm"
            >
              x
            </button>
          </div>
        ))}
        <button
          onClick={() => onChange({ ...data, pros: [...data.pros, ""] })}
          className="text-xs text-green-600 hover:underline mt-1"
        >
          + Add pro
        </button>
      </div>

      {/* Cons */}
      <div>
        <h4 className="text-xs font-semibold text-red-700 mb-2 flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
          Cons
        </h4>
        {data.cons.map((con, i) => (
          <div key={i} className="flex gap-1 mb-1">
            <span className="text-red-500 mt-1">&ndash;</span>
            <input
              type="text"
              value={con}
              onChange={(e) => updateCon(i, e.target.value)}
              className="flex-1 px-2 py-1 border border-red-200 rounded text-sm focus:ring-2 focus:ring-red-400 focus:border-red-400"
            />
            <button
              onClick={() => onChange({ ...data, cons: data.cons.filter((_, j) => j !== i) })}
              className="text-red-300 hover:text-red-500 text-sm"
            >
              x
            </button>
          </div>
        ))}
        <button
          onClick={() => onChange({ ...data, cons: [...data.cons, ""] })}
          className="text-xs text-red-600 hover:underline mt-1"
        >
          + Add con
        </button>
      </div>
    </SectionCard>
  );
}

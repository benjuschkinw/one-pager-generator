"use client";

import { InvestmentCriteria, CriterionStatus, CRITERIA_LABELS } from "@/lib/types";
import SectionCard from "./SectionCard";

interface Props {
  data: InvestmentCriteria;
  onChange: (data: InvestmentCriteria) => void;
}

const STATUS_CYCLE: CriterionStatus[] = ["fulfilled", "questions", "not_interest"];

const STATUS_DISPLAY: Record<CriterionStatus, { label: string; className: string }> = {
  fulfilled: { label: "Fulfilled", className: "bg-green-100 text-green-800 border-green-300" },
  questions: { label: "Questions", className: "bg-yellow-100 text-yellow-800 border-yellow-300" },
  not_interest: { label: "N/A", className: "bg-gray-100 text-gray-500 border-gray-300" },
};

export default function CriteriaSection({ data, onChange }: Props) {
  const toggleCriterion = (key: keyof InvestmentCriteria) => {
    const current = data[key];
    const currentIndex = STATUS_CYCLE.indexOf(current);
    const next = STATUS_CYCLE[(currentIndex + 1) % STATUS_CYCLE.length];
    onChange({ ...data, [key]: next });
  };

  const criteriaKeys = Object.keys(CRITERIA_LABELS) as (keyof InvestmentCriteria)[];

  return (
    <SectionCard title="Investment Criteria">
      <div className="space-y-1">
        {criteriaKeys.map((key) => {
          const status = data[key];
          const display = STATUS_DISPLAY[status];
          return (
            <div key={key} className="flex items-center justify-between py-1 border-b border-gray-50 last:border-0">
              <span className="text-sm text-gray-700">{CRITERIA_LABELS[key]}</span>
              <button
                onClick={() => toggleCriterion(key)}
                className={`px-3 py-0.5 rounded text-xs font-medium border transition-all ${display.className}`}
              >
                {display.label}
              </button>
            </div>
          );
        })}
      </div>
      <p className="text-xs text-gray-400 mt-2">
        Click to cycle: Fulfilled &rarr; Questions &rarr; N/A
      </p>
    </SectionCard>
  );
}

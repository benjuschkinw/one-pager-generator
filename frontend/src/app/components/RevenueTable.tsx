"use client";

import { RevenueSplit, RevenueSegment } from "@/lib/types";
import SectionCard from "./SectionCard";

interface Props {
  data: RevenueSplit;
  onChange: (data: RevenueSplit) => void;
}

export default function RevenueTable({ data, onChange }: Props) {
  const updateSegment = (index: number, field: keyof RevenueSegment, value: string) => {
    const segments = [...data.segments];
    if (field === "pct") {
      segments[index] = { ...segments[index], [field]: parseFloat(value) || 0 };
    } else {
      segments[index] = { ...segments[index], [field]: value };
    }
    onChange({ ...data, segments });
  };

  const addSegment = () => {
    onChange({
      ...data,
      segments: [...data.segments, { name: "", pct: 0, growth: "" }],
    });
  };

  const removeSegment = (index: number) => {
    onChange({
      ...data,
      segments: data.segments.filter((_, i) => i !== index),
    });
  };

  const totalPct = data.segments.reduce((sum, s) => sum + s.pct, 0);

  return (
    <SectionCard title="Revenue Split">
      <div className="mb-3">
        <label className="block text-xs font-medium text-gray-500 mb-1">Total Revenue</label>
        <input
          type="text"
          value={data.total}
          onChange={(e) => onChange({ ...data, total: e.target.value })}
          placeholder="EUR 4.3m"
          className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-cc-mid focus:border-cc-mid"
        />
      </div>

      <table className="w-full text-sm">
        <thead>
          <tr className="text-xs text-gray-500 border-b">
            <th className="text-left py-1 font-medium">Segment</th>
            <th className="text-right py-1 font-medium w-16">%</th>
            <th className="text-right py-1 font-medium w-20">Growth</th>
            <th className="w-8"></th>
          </tr>
        </thead>
        <tbody>
          {data.segments.map((seg, i) => (
            <tr key={i} className="border-b border-gray-50">
              <td className="py-1 pr-1">
                <input
                  type="text"
                  value={seg.name}
                  onChange={(e) => updateSegment(i, "name", e.target.value)}
                  className="w-full px-1 py-0.5 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid"
                />
              </td>
              <td className="py-1 px-1">
                <input
                  type="number"
                  value={seg.pct}
                  onChange={(e) => updateSegment(i, "pct", e.target.value)}
                  className="w-full px-1 py-0.5 border border-gray-200 rounded text-sm text-right focus:ring-1 focus:ring-cc-mid"
                />
              </td>
              <td className="py-1 px-1">
                <input
                  type="text"
                  value={seg.growth || ""}
                  onChange={(e) => updateSegment(i, "growth", e.target.value)}
                  placeholder="+X%"
                  className="w-full px-1 py-0.5 border border-gray-200 rounded text-sm text-right focus:ring-1 focus:ring-cc-mid"
                />
              </td>
              <td className="py-1">
                <button onClick={() => removeSegment(i)} className="text-red-300 hover:text-red-500 text-xs">
                  x
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="flex items-center justify-between mt-2">
        <button onClick={addSegment} className="text-xs text-cc-mid hover:underline">
          + Add segment
        </button>
        <span className={`text-xs font-medium ${Math.abs(totalPct - 100) > 1 ? "text-red-500" : "text-green-600"}`}>
          Total: {totalPct}%
        </span>
      </div>
    </SectionCard>
  );
}

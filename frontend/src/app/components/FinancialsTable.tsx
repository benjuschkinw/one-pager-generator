"use client";

import { Financials } from "@/lib/types";
import SectionCard from "./SectionCard";

interface Props {
  data: Financials;
  onChange: (data: Financials) => void;
}

export default function FinancialsTable({ data, onChange }: Props) {
  const updateYear = (index: number, value: string) => {
    const years = [...data.years];
    years[index] = value;
    onChange({ ...data, years });
  };

  const updateValue = (
    field: "revenue" | "ebitda" | "ebitda_margin",
    index: number,
    value: string
  ) => {
    const arr = [...data[field]];
    arr[index] = value === "" ? null : parseFloat(value);
    onChange({ ...data, [field]: arr });
  };

  const addYear = () => {
    onChange({
      ...data,
      years: [...data.years, ""],
      revenue: [...data.revenue, null],
      ebitda: [...data.ebitda, null],
      ebitda_margin: [...data.ebitda_margin, null],
    });
  };

  const removeYear = (index: number) => {
    onChange({
      ...data,
      years: data.years.filter((_, i) => i !== index),
      revenue: data.revenue.filter((_, i) => i !== index),
      ebitda: data.ebitda.filter((_, i) => i !== index),
      ebitda_margin: data.ebitda_margin.filter((_, i) => i !== index),
    });
  };

  return (
    <SectionCard title="Key Financials">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 border-b">
              <th className="text-left py-1 font-medium w-24">Metric</th>
              {data.years.map((year, i) => (
                <th key={i} className="text-center py-1 font-medium w-16">
                  <input
                    type="text"
                    value={year}
                    onChange={(e) => updateYear(i, e.target.value)}
                    className="w-14 text-center px-1 py-0.5 border border-gray-200 rounded text-xs focus:ring-1 focus:ring-cc-mid"
                    placeholder="25A"
                  />
                </th>
              ))}
              <th className="w-8"></th>
            </tr>
          </thead>
          <tbody>
            {/* Revenue row */}
            <tr className="border-b border-gray-50">
              <td className="py-1 text-xs font-medium text-cc-dark">Revenue (EUR m)</td>
              {data.revenue.map((val, i) => (
                <td key={i} className="py-1 px-0.5">
                  <input
                    type="number"
                    step="0.1"
                    value={val ?? ""}
                    onChange={(e) => updateValue("revenue", i, e.target.value)}
                    className="w-14 text-center px-1 py-0.5 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid"
                  />
                </td>
              ))}
              <td></td>
            </tr>

            {/* EBITDA row */}
            <tr className="border-b border-gray-50">
              <td className="py-1 text-xs font-medium text-cc-dark">EBITDA (EUR m)</td>
              {data.ebitda.map((val, i) => (
                <td key={i} className="py-1 px-0.5">
                  <input
                    type="number"
                    step="0.1"
                    value={val ?? ""}
                    onChange={(e) => updateValue("ebitda", i, e.target.value)}
                    className="w-14 text-center px-1 py-0.5 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid"
                  />
                </td>
              ))}
              <td></td>
            </tr>

            {/* EBITDA Margin row */}
            <tr>
              <td className="py-1 text-xs font-medium text-cc-mid">EBITDA Margin</td>
              {data.ebitda_margin.map((val, i) => (
                <td key={i} className="py-1 px-0.5">
                  <input
                    type="number"
                    step="0.01"
                    value={val ?? ""}
                    onChange={(e) => updateValue("ebitda_margin", i, e.target.value)}
                    placeholder="0.xx"
                    className="w-14 text-center px-1 py-0.5 border border-gray-200 rounded text-sm focus:ring-1 focus:ring-cc-mid"
                  />
                </td>
              ))}
              <td></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between mt-2">
        <button onClick={addYear} className="text-xs text-cc-mid hover:underline">
          + Add year
        </button>
        {data.years.length > 0 && (
          <button
            onClick={() => removeYear(data.years.length - 1)}
            className="text-xs text-red-400 hover:underline"
          >
            Remove last year
          </button>
        )}
      </div>

      <div className="mt-2">
        <label className="block text-xs font-medium text-gray-500 mb-1">D&A %</label>
        <input
          type="number"
          step="0.01"
          value={data.da_pct ?? ""}
          onChange={(e) => onChange({ ...data, da_pct: e.target.value === "" ? null : parseFloat(e.target.value) })}
          placeholder="0.06"
          className="w-20 px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-cc-mid focus:border-cc-mid"
        />
      </div>
    </SectionCard>
  );
}

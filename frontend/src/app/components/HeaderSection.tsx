"use client";

import { Header } from "@/lib/types";
import SectionCard from "./SectionCard";

interface Props {
  data: Header;
  thesis: string;
  onChange: (data: Header) => void;
  onThesisChange: (thesis: string) => void;
}

export default function HeaderSection({ data, thesis, onChange, onThesisChange }: Props) {
  return (
    <SectionCard title="Header">
      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Company Name</label>
          <input
            type="text"
            value={data.company_name}
            onChange={(e) => onChange({ ...data, company_name: e.target.value })}
            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm font-bold focus:ring-2 focus:ring-cc-mid focus:border-cc-mid"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Tagline</label>
          <input
            type="text"
            value={data.tagline}
            onChange={(e) => onChange({ ...data, tagline: e.target.value })}
            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-cc-mid focus:border-cc-mid"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Investment Thesis</label>
          <textarea
            value={thesis}
            onChange={(e) => onThesisChange(e.target.value)}
            rows={2}
            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-cc-mid focus:border-cc-mid"
          />
        </div>
      </div>
    </SectionCard>
  );
}

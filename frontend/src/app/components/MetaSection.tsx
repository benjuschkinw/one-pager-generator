"use client";

import { Meta } from "@/lib/types";
import SectionCard from "./SectionCard";

interface Props {
  data: Meta;
  onChange: (data: Meta) => void;
}

export default function MetaSection({ data, onChange }: Props) {
  const update = (field: keyof Meta, value: string) => {
    onChange({ ...data, [field]: value });
  };

  return (
    <SectionCard title="Status">
      <div className="grid grid-cols-2 gap-3">
        <Field label="Source" value={data.source} onChange={(v) => update("source", v)} />
        <Field label="IM Received" value={data.im_received} onChange={(v) => update("im_received", v)} placeholder="DD.MM.YYYY" />
        <Field label="LOI Deadline" value={data.loi_deadline} onChange={(v) => update("loi_deadline", v)} placeholder="DD.MM.YYYY" />
        <Field label="Status" value={data.status} onChange={(v) => update("status", v)} />
      </div>
    </SectionCard>
  );
}

function Field({ label, value, onChange, placeholder }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-cc-mid focus:border-cc-mid"
      />
    </div>
  );
}

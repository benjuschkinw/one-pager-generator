"use client";

import { TrendsDrivers } from "@/lib/types";
import MarketSectionCard from "./MarketSectionCard";
import MarketBulletEditor from "./MarketBulletEditor";

interface Props {
  data: TrendsDrivers;
  onChange: (data: TrendsDrivers) => void;
}

export default function TrendsSection({ data, onChange }: Props) {
  return (
    <MarketSectionCard title="Trends & Drivers" slideNumber={5}>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <MarketBulletEditor label="Growth Drivers" items={data.growth_drivers}
          onChange={(growth_drivers) => onChange({ ...data, growth_drivers })} placeholder="Add driver..." />
        <MarketBulletEditor label="Headwinds" items={data.headwinds}
          onChange={(headwinds) => onChange({ ...data, headwinds })} placeholder="Add headwind..." />
        <MarketBulletEditor label="Technological Shifts" items={data.technological_shifts}
          onChange={(technological_shifts) => onChange({ ...data, technological_shifts })} placeholder="Add shift..." />
        <MarketBulletEditor label="Regulatory Changes" items={data.regulatory_changes}
          onChange={(regulatory_changes) => onChange({ ...data, regulatory_changes })} placeholder="Add change..." />
      </div>
    </MarketSectionCard>
  );
}

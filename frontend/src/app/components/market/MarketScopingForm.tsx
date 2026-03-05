"use client";

import { MarketScopingContext } from "@/lib/types";

interface Props {
  marketName: string;
  scoping: MarketScopingContext;
  onChange: (scoping: MarketScopingContext) => void;
  onSubmit: () => void;
  onBack: () => void;
  loading: boolean;
}

const VALUE_CHAIN_OPTIONS = [
  { value: "entire", label: "Entire Value Chain" },
  { value: "production", label: "Production / Manufacturing" },
  { value: "distribution", label: "Distribution / Wholesale" },
  { value: "retail", label: "Retail / End Sales" },
  { value: "services", label: "Services" },
];

const TIME_HORIZON_OPTIONS = [
  { value: "current", label: "Current (last 12-24 months) + 5-year forecast" },
  { value: "historical_5y", label: "Historical 5 years + 5-year forecast (2020-2030)" },
  { value: "historical_10y", label: "Historical 10 years + 5-year forecast (2015-2030)" },
  { value: "forward_only", label: "Forward-looking only (next 5-10 years)" },
];

const CUSTOMER_TYPE_OPTIONS = [
  { value: "b2b", label: "B2B (Business Customers)" },
  { value: "b2c", label: "B2C (End Consumers)" },
  { value: "b2b2c", label: "B2B2C (Both)" },
  { value: "b2g", label: "B2G (Public Sector)" },
];

const METRIC_OPTIONS = [
  { value: "value", label: "Revenue / Value" },
  { value: "volume", label: "Volume / Units" },
  { value: "customers", label: "Number of Customers / Users" },
  { value: "value_and_volume", label: "Revenue + Volume" },
];

const PURPOSE_OPTIONS = [
  { value: "market_entry", label: "Market Entry Decision (PE / M&A)" },
  { value: "competitive_strategy", label: "Competitive Strategy" },
  { value: "growth_potential", label: "Identify Growth Potential" },
  { value: "buy_and_build", label: "Validate Buy & Build Thesis" },
  { value: "general", label: "General Market Overview" },
];

export default function MarketScopingForm({ marketName, scoping, onChange, onSubmit, onBack, loading }: Props) {
  const update = (patch: Partial<MarketScopingContext>) => onChange({ ...scoping, ...patch });

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center gap-3 pb-3 border-b border-gray-100">
        <button onClick={onBack} aria-label="Go back" className="text-gray-400 hover:text-cc-mid transition-colors">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div>
          <h3 className="text-sm font-semibold text-cc-dark">Scoping: {marketName}</h3>
          <p className="text-xs text-gray-400">
            Define the scope of analysis for targeted, precise results.
          </p>
        </div>
      </div>

      {/* 1. Product Scope */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">1</span>
          <label className="text-sm font-medium text-gray-700">Product Scope</label>
        </div>
        <textarea
          value={scoping.product_scope}
          onChange={(e) => update({ product_scope: e.target.value })}
          placeholder="What exactly is included / excluded? e.g. 'Only non-alcoholic beverages, excluding water' or 'Full IT security segment incl. managed services'"
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-cc-mid/30 focus:border-cc-mid transition-all placeholder:text-gray-400"
        />
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Value Chain Focus</label>
          <select
            value={scoping.value_chain_focus}
            onChange={(e) => update({ value_chain_focus: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-cc-mid/30 focus:border-cc-mid transition-all"
          >
            {VALUE_CHAIN_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* 2. Geography & Time */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">2</span>
          <label className="text-sm font-medium text-gray-700">Geography & Time Horizon</label>
        </div>
        <input
          type="text"
          value={scoping.geographic_detail}
          onChange={(e) => update({ geographic_detail: e.target.value })}
          placeholder="Further narrowing, e.g. 'urban areas only', 'focus on Southern Germany', 'excl. Switzerland'"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-cc-mid/30 focus:border-cc-mid transition-all placeholder:text-gray-400"
        />
        <select
          value={scoping.time_horizon}
          onChange={(e) => update({ time_horizon: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-cc-mid/30 focus:border-cc-mid transition-all"
        >
          {TIME_HORIZON_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* 3. Customer Segmentation */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">3</span>
          <label className="text-sm font-medium text-gray-700">Target Audience</label>
        </div>
        <select
          value={scoping.customer_type}
          onChange={(e) => update({ customer_type: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-cc-mid/30 focus:border-cc-mid transition-all"
        >
          {CUSTOMER_TYPE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <input
          type="text"
          value={scoping.customer_detail}
          onChange={(e) => update({ customer_detail: e.target.value })}
          placeholder="Additional criteria, e.g. 'SMEs with 10-250 employees', 'Age 25-45', 'Industrial companies'"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-cc-mid/30 focus:border-cc-mid transition-all placeholder:text-gray-400"
        />
      </div>

      {/* 4. Strategic Context & Metrics */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">4</span>
          <label className="text-sm font-medium text-gray-700">Strategic Context</label>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Market Size Metric</label>
            <select
              value={scoping.market_metric}
              onChange={(e) => update({ market_metric: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-cc-mid/30 focus:border-cc-mid transition-all"
            >
              {METRIC_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Study Purpose</label>
            <select
              value={scoping.study_purpose}
              onChange={(e) => update({ study_purpose: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-cc-mid/30 focus:border-cc-mid transition-all"
            >
              {PURPOSE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Submit */}
      <button
        onClick={onSubmit}
        disabled={loading}
        className="w-full py-2.5 px-6 bg-cc-dark text-white rounded-lg font-medium text-sm
                   hover:bg-cc-mid transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                   flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Starting market analysis...
          </>
        ) : (
          <>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Start Analysis
          </>
        )}
      </button>
    </div>
  );
}

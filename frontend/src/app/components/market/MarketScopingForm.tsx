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
  { value: "entire", label: "Gesamte Wertschöpfungskette" },
  { value: "production", label: "Produktion / Herstellung" },
  { value: "distribution", label: "Distribution / Großhandel" },
  { value: "retail", label: "Einzelhandel / Endvertrieb" },
  { value: "services", label: "Services / Dienstleistungen" },
];

const TIME_HORIZON_OPTIONS = [
  { value: "current", label: "Aktuell (letzte 12-24 Monate) + Prognose 5 Jahre" },
  { value: "historical_5y", label: "Historisch 5 Jahre + Prognose 5 Jahre (2020-2030)" },
  { value: "historical_10y", label: "Historisch 10 Jahre + Prognose 5 Jahre (2015-2030)" },
  { value: "forward_only", label: "Nur Zukunft / Prognose (nächste 5-10 Jahre)" },
];

const CUSTOMER_TYPE_OPTIONS = [
  { value: "b2b", label: "B2B (Geschäftskunden)" },
  { value: "b2c", label: "B2C (Endverbraucher)" },
  { value: "b2b2c", label: "B2B2C (beide)" },
  { value: "b2g", label: "B2G (öffentliche Auftraggeber)" },
];

const METRIC_OPTIONS = [
  { value: "value", label: "Umsatzwert (Revenue / Value)" },
  { value: "volume", label: "Absatzmenge (Volume / Units)" },
  { value: "customers", label: "Anzahl Kunden / Nutzer" },
  { value: "value_and_volume", label: "Umsatz + Menge" },
];

const PURPOSE_OPTIONS = [
  { value: "market_entry", label: "Markteintrittsentscheidung (PE / M&A)" },
  { value: "competitive_strategy", label: "Wettbewerbsstrategie" },
  { value: "growth_potential", label: "Marktwachstumspotenziale identifizieren" },
  { value: "buy_and_build", label: "Buy & Build Thesis validieren" },
  { value: "general", label: "Allgemeine Marktübersicht" },
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
            Präzisiere den Umfang der Analyse, um zielgenaue Ergebnisse zu erhalten.
          </p>
        </div>
      </div>

      {/* 1. Product Scope */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">1</span>
          <label className="text-sm font-medium text-gray-700">Produkt-Scope</label>
        </div>
        <textarea
          value={scoping.product_scope}
          onChange={(e) => update({ product_scope: e.target.value })}
          placeholder="Was genau ist inkludiert / ausgeschlossen? z.B. 'Nur alkoholfreie Erfrischungsgetränke, ohne Wasser und Säfte' oder 'Gesamtes IT-Security-Segment inkl. Managed Services'"
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-cc-mid/30 focus:border-cc-mid transition-all placeholder:text-gray-400"
        />
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Wertschöpfungsstufe</label>
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
          <label className="text-sm font-medium text-gray-700">Geografie & Zeithorizont</label>
        </div>
        <input
          type="text"
          value={scoping.geographic_detail}
          onChange={(e) => update({ geographic_detail: e.target.value })}
          placeholder="Weitere Eingrenzung, z.B. 'nur urbane Gebiete', 'Fokus auf Süddeutschland', 'exkl. Schweiz'"
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
          <label className="text-sm font-medium text-gray-700">Zielgruppen-Definition</label>
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
          placeholder="Weitere Merkmale, z.B. 'KMU mit 10-250 MA', 'Alter 25-45', 'Industrieunternehmen'"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-cc-mid/30 focus:border-cc-mid transition-all placeholder:text-gray-400"
        />
      </div>

      {/* 4. Strategic Context & Metrics */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">4</span>
          <label className="text-sm font-medium text-gray-700">Strategischer Kontext</label>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Maßeinheit Marktgröße</label>
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
            <label className="text-xs text-gray-500 mb-1 block">Ziel der Studie</label>
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
            Marktanalyse wird gestartet...
          </>
        ) : (
          <>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Analyse starten
          </>
        )}
      </button>
    </div>
  );
}

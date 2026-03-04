"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { OnePagerData, VerificationResult, EMPTY_ONE_PAGER } from "@/lib/types";
import HeaderSection from "../components/HeaderSection";
import MetaSection from "../components/MetaSection";
import KeyFactsSection from "../components/KeyFactsSection";
import BulletEditor from "../components/BulletEditor";
import RationaleSection from "../components/RationaleSection";
import CriteriaSection from "../components/CriteriaSection";
import RevenueTable from "../components/RevenueTable";
import FinancialsTable from "../components/FinancialsTable";
import GenerateButton from "../components/GenerateButton";
import VerificationBanner from "../components/VerificationBanner";

export default function EditorPage() {
  const router = useRouter();
  const [data, setData] = useState<OnePagerData>(EMPTY_ONE_PAGER);
  const [verification, setVerification] = useState<VerificationResult | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem("onePagerData");
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as Partial<OnePagerData>;
        setData({
          meta: { ...EMPTY_ONE_PAGER.meta, ...parsed.meta },
          header: { ...EMPTY_ONE_PAGER.header, ...parsed.header },
          investment_thesis: parsed.investment_thesis ?? EMPTY_ONE_PAGER.investment_thesis,
          key_facts: { ...EMPTY_ONE_PAGER.key_facts, ...parsed.key_facts },
          description: parsed.description ?? EMPTY_ONE_PAGER.description,
          product_portfolio: parsed.product_portfolio ?? EMPTY_ONE_PAGER.product_portfolio,
          investment_rationale: { ...EMPTY_ONE_PAGER.investment_rationale, ...parsed.investment_rationale },
          revenue_split: { ...EMPTY_ONE_PAGER.revenue_split, ...parsed.revenue_split },
          financials: { ...EMPTY_ONE_PAGER.financials, ...parsed.financials },
          investment_criteria: { ...EMPTY_ONE_PAGER.investment_criteria, ...parsed.investment_criteria },
        });
      } catch {
        /* ignore malformed JSON */
      }
    }
    const storedVerification = sessionStorage.getItem("verification");
    if (storedVerification) {
      try {
        setVerification(JSON.parse(storedVerification) as VerificationResult);
      } catch {
        /* ignore malformed JSON */
      }
    }
    setLoaded(true);
  }, []);

  if (!loaded) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin h-8 w-8 border-4 border-cc-mid border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div>
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push("/")}
            className="text-xs text-gray-400 hover:text-cc-mid transition-colors flex items-center gap-1"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </button>
          <div className="h-4 w-px bg-gray-200" />
          <h2 className="text-lg font-semibold text-cc-dark">
            {data.header.company_name || "New One-Pager"}
          </h2>
        </div>

        <button
          onClick={() => {
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${data.header.company_name || "one_pager"}_data.json`;
            a.click();
            URL.revokeObjectURL(url);
          }}
          className="text-xs text-gray-400 hover:text-cc-mid border border-gray-200 px-3 py-1.5 rounded-lg
                     hover:border-cc-mid/30 transition-all flex items-center gap-1.5"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Export JSON
        </button>
      </div>

      {/* Verification Banner */}
      {verification && <VerificationBanner verification={verification} />}

      {/* 3-column grid matching the slide layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Column 1: Key Facts + Criteria + Status */}
        <div className="space-y-4">
          <HeaderSection
            data={data.header}
            thesis={data.investment_thesis}
            onChange={(header) => setData({ ...data, header })}
            onThesisChange={(thesis) => setData({ ...data, investment_thesis: thesis })}
          />
          <KeyFactsSection
            data={data.key_facts}
            onChange={(key_facts) => setData({ ...data, key_facts })}
          />
          <CriteriaSection
            data={data.investment_criteria}
            onChange={(investment_criteria) => setData({ ...data, investment_criteria })}
          />
          <MetaSection
            data={data.meta}
            onChange={(meta) => setData({ ...data, meta })}
          />
        </div>

        {/* Column 2: Description + Portfolio + Revenue Split */}
        <div className="space-y-4">
          <BulletEditor
            title="Description"
            items={data.description}
            onChange={(description) => setData({ ...data, description })}
          />
          <BulletEditor
            title="Product Portfolio"
            items={data.product_portfolio}
            onChange={(product_portfolio) => setData({ ...data, product_portfolio })}
          />
          <RevenueTable
            data={data.revenue_split}
            onChange={(revenue_split) => setData({ ...data, revenue_split })}
          />
        </div>

        {/* Column 3: Rationale + Financials */}
        <div className="space-y-4">
          <RationaleSection
            data={data.investment_rationale}
            onChange={(investment_rationale) => setData({ ...data, investment_rationale })}
          />
          <FinancialsTable
            data={data.financials}
            onChange={(financials) => setData({ ...data, financials })}
          />
        </div>
      </div>

      {/* Generate Button (sticky bottom) */}
      <GenerateButton data={data} />
    </div>
  );
}

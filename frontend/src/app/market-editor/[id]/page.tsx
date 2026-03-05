"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { MarketStudyData, EMPTY_MARKET_STUDY, Job } from "@/lib/types";
import { getJob, saveMarketData, generateMarketPptx } from "@/lib/api";
import DeepResearchProgress from "../../components/DeepResearchProgress";
import DeepResearchResults from "../../components/DeepResearchResults";
import MarketSectionCard from "../../components/market/MarketSectionCard";
import ExecutiveSummarySection from "../../components/market/ExecutiveSummarySection";
import MarketSizingSection from "../../components/market/MarketSizingSection";
import SegmentationSection from "../../components/market/SegmentationSection";
import CompetitiveLandscapeSection from "../../components/market/CompetitiveLandscapeSection";
import TrendsSection from "../../components/market/TrendsSection";
import PestelSection from "../../components/market/PestelSection";
import PortersSection from "../../components/market/PortersSection";
import ValueChainSection from "../../components/market/ValueChainSection";
import BuyAndBuildSection from "../../components/market/BuyAndBuildSection";
import StrategicImplicationsSection from "../../components/market/StrategicImplicationsSection";

export default function MarketEditorPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;

  const [data, setData] = useState<MarketStudyData>(EMPTY_MARKET_STUDY);
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);
  const [genSuccess, setGenSuccess] = useState(false);
  const [researchActive, setResearchActive] = useState(false);

  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadJob = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const jobData = await getJob(jobId);
      setJob(jobData);

      const marketData = jobData.edited_market_data || jobData.market_study_data;
      if (marketData) {
        // Deep merge: preserve nested defaults for any missing sub-objects
        const merged = { ...EMPTY_MARKET_STUDY };
        for (const key of Object.keys(merged) as (keyof typeof merged)[]) {
          if (marketData[key] !== undefined && marketData[key] !== null) {
            const empty = merged[key];
            const incoming = marketData[key];
            if (typeof empty === "object" && !Array.isArray(empty) && typeof incoming === "object" && !Array.isArray(incoming)) {
              (merged as Record<string, unknown>)[key] = { ...empty, ...incoming };
            } else {
              (merged as Record<string, unknown>)[key] = incoming;
            }
          }
        }
        setData(merged);
      }

      // If job is still researching, show progress
      if (jobData.status === "researching" && jobData.research_mode === "market") {
        setResearchActive(true);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load job");
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    loadJob();
  }, [loadJob]);

  const debouncedSave = useCallback(
    (newData: MarketStudyData) => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
      saveTimerRef.current = setTimeout(async () => {
        try {
          setSaving(true);
          setSaveError(null);
          await saveMarketData(jobId, newData);
        } catch (e) {
          setSaveError(e instanceof Error ? e.message : "Save failed");
        } finally {
          setSaving(false);
        }
      }, 500);
    },
    [jobId]
  );

  useEffect(() => {
    return () => { if (saveTimerRef.current) clearTimeout(saveTimerRef.current); };
  }, []);

  function updateData(newData: MarketStudyData) {
    setData(newData);
    debouncedSave(newData);
  }

  async function handleGenerate() {
    setGenerating(true);
    setGenError(null);
    setGenSuccess(false);
    try {
      await generateMarketPptx(jobId);
      setGenSuccess(true);
      setTimeout(() => setGenSuccess(false), 3000);
    } catch (e) {
      setGenError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-cc-mid border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-sm text-gray-500">Loading market study...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-lg mx-auto mt-16 text-center">
        <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h2 className="text-lg font-semibold text-cc-dark mb-2">Job Not Found</h2>
        <p className="text-sm text-gray-500 mb-6">{error}</p>
        <button onClick={() => router.push("/jobs")} className="text-sm text-cc-mid hover:underline">
          Go to Job History
        </button>
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
            aria-label="Go back to home"
            className="text-xs text-gray-400 hover:text-cc-mid transition-colors flex items-center gap-1"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </button>
          <div className="h-4 w-px bg-gray-200" />
          <div>
            <h2 className="text-lg font-semibold text-cc-dark">
              {data.meta.market_name || "Market Study"}
            </h2>
            <p className="text-xs text-gray-400">{data.meta.region} | 10-Slide Market Study</p>
          </div>

          {saving && (
            <span className="text-xs text-gray-400 flex items-center gap-1">
              <div className="w-1.5 h-1.5 bg-yellow-400 rounded-full animate-pulse" />
              Saving...
            </span>
          )}
          {saveError && (
            <span className="text-xs text-red-500">Save failed</span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `Market_Study_${data.meta.market_name || "export"}.json`;
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
      </div>

      {/* Research Progress */}
      {researchActive && (
        <div className="mb-6">
          <DeepResearchProgress
            jobId={jobId}
            onComplete={async () => {
              setResearchActive(false);
              const updatedJob = await getJob(jobId);
              setJob(updatedJob);
              const md = updatedJob.edited_market_data || updatedJob.market_study_data;
              if (md) {
                const m = { ...EMPTY_MARKET_STUDY };
                for (const key of Object.keys(m) as (keyof typeof m)[]) {
                  if (md[key] !== undefined && md[key] !== null) {
                    const empty = m[key];
                    const incoming = md[key];
                    if (typeof empty === "object" && !Array.isArray(empty) && typeof incoming === "object" && !Array.isArray(incoming)) {
                      (m as Record<string, unknown>)[key] = { ...empty, ...incoming };
                    } else {
                      (m as Record<string, unknown>)[key] = incoming;
                    }
                  }
                }
                setData(m);
              }
            }}
            onError={(msg) => {
              setResearchActive(false);
              setGenError(msg);
            }}
          />
        </div>
      )}

      {/* Deep Research Results */}
      {job?.deep_research_steps && job.deep_research_steps.length > 0 && (
        <div className="mb-6">
          <DeepResearchResults steps={job.deep_research_steps} jobId={jobId} />
        </div>
      )}

      {/* Section Cards — 2-column grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ExecutiveSummarySection
          data={data.executive_summary}
          onChange={(executive_summary) => updateData({ ...data, executive_summary })}
        />
        <MarketSizingSection
          data={data.market_sizing}
          onChange={(market_sizing) => updateData({ ...data, market_sizing })}
        />
        <SegmentationSection
          segments={data.market_segments}
          onChange={(market_segments) => updateData({ ...data, market_segments })}
        />
        <CompetitiveLandscapeSection
          data={data.competitive_landscape}
          onChange={(competitive_landscape) => updateData({ ...data, competitive_landscape })}
        />
        <TrendsSection
          data={data.trends_drivers}
          onChange={(trends_drivers) => updateData({ ...data, trends_drivers })}
        />
        <PestelSection
          data={data.pestel}
          onChange={(pestel) => updateData({ ...data, pestel })}
        />
        <PortersSection
          data={data.porters_five_forces}
          onChange={(porters_five_forces) => updateData({ ...data, porters_five_forces })}
        />
        <ValueChainSection
          data={data.value_chain}
          onChange={(value_chain) => updateData({ ...data, value_chain })}
        />
        <BuyAndBuildSection
          data={data.buy_and_build}
          onChange={(buy_and_build) => updateData({ ...data, buy_and_build })}
        />
        <StrategicImplicationsSection
          data={data.strategic_implications}
          onChange={(strategic_implications) => updateData({ ...data, strategic_implications })}
        />
      </div>

      {/* Generate Button (sticky bottom) */}
      <div className="sticky bottom-0 bg-white/95 backdrop-blur-sm border-t border-gray-200 py-3 px-6 -mx-6 mt-8 shadow-[0_-4px_12px_rgba(0,0,0,0.05)]">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="text-sm">
            {genError && (
              <div className="flex items-center gap-1.5 text-red-600">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01" />
                </svg>
                {genError}
              </div>
            )}
            {genSuccess && (
              <div className="flex items-center gap-1.5 text-green-600 font-medium">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                PPTX downloaded successfully
              </div>
            )}
          </div>
          <button
            onClick={handleGenerate}
            disabled={generating || !data.meta.market_name}
            className="py-2.5 px-6 bg-cc-dark text-white rounded-lg font-medium text-sm
                       hover:bg-cc-mid transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                       flex items-center gap-2"
          >
            {generating ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Generating...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Generate Market Study PPTX
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

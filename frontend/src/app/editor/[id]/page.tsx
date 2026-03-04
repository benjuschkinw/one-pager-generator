"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { OnePagerData, VerificationResult, EMPTY_ONE_PAGER, Job } from "@/lib/types";
import { getJob, saveJobData, generateJobPptx, getJobImUrl } from "@/lib/api";
import HeaderSection from "../../components/HeaderSection";
import MetaSection from "../../components/MetaSection";
import KeyFactsSection from "../../components/KeyFactsSection";
import BulletEditor from "../../components/BulletEditor";
import RationaleSection from "../../components/RationaleSection";
import CriteriaSection from "../../components/CriteriaSection";
import RevenueTable from "../../components/RevenueTable";
import FinancialsTable from "../../components/FinancialsTable";
import VerificationBanner from "../../components/VerificationBanner";
import DeepResearchProgress from "../../components/DeepResearchProgress";
import DeepResearchResults from "../../components/DeepResearchResults";

export default function JobEditorPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const jobId = params.id as string;
  const isDeepResearch = searchParams.get("deep") === "true";

  const [data, setData] = useState<OnePagerData>(EMPTY_ONE_PAGER);
  const [verification, setVerification] = useState<VerificationResult | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);
  const [genSuccess, setGenSuccess] = useState(false);
  const [deepResearchActive, setDeepResearchActive] = useState(isDeepResearch);
  const [showDeepResults, setShowDeepResults] = useState(false);

  // Debounce timer ref
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load / reload job data
  const loadJob = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const jobData = await getJob(jobId);
      setJob(jobData);

      // Use edited_data if present, fall back to research_data
      const onePagerData = jobData.edited_data || jobData.research_data;
      if (onePagerData) {
        setData({
          meta: { ...EMPTY_ONE_PAGER.meta, ...onePagerData.meta },
          header: { ...EMPTY_ONE_PAGER.header, ...onePagerData.header },
          investment_thesis: onePagerData.investment_thesis ?? EMPTY_ONE_PAGER.investment_thesis,
          key_facts: { ...EMPTY_ONE_PAGER.key_facts, ...onePagerData.key_facts },
          description: onePagerData.description ?? EMPTY_ONE_PAGER.description,
          product_portfolio: onePagerData.product_portfolio ?? EMPTY_ONE_PAGER.product_portfolio,
          investment_rationale: { ...EMPTY_ONE_PAGER.investment_rationale, ...onePagerData.investment_rationale },
          revenue_split: { ...EMPTY_ONE_PAGER.revenue_split, ...onePagerData.revenue_split },
          financials: { ...EMPTY_ONE_PAGER.financials, ...onePagerData.financials },
          investment_criteria: { ...EMPTY_ONE_PAGER.investment_criteria, ...onePagerData.investment_criteria },
        });
      }

      if (jobData.verification) {
        setVerification(jobData.verification);
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

  // Debounced auto-save
  const debouncedSave = useCallback(
    (newData: OnePagerData) => {
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current);
      }
      saveTimerRef.current = setTimeout(async () => {
        try {
          setSaving(true);
          setSaveError(null);
          await saveJobData(jobId, newData);
        } catch (e) {
          setSaveError(e instanceof Error ? e.message : "Save failed");
        } finally {
          setSaving(false);
        }
      }, 500);
    },
    [jobId]
  );

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current);
      }
    };
  }, []);

  function updateData(newData: OnePagerData) {
    setData(newData);
    debouncedSave(newData);
  }

  async function handleGenerate() {
    setGenerating(true);
    setGenError(null);
    setGenSuccess(false);

    try {
      await generateJobPptx(jobId);
      setGenSuccess(true);
      setTimeout(() => setGenSuccess(false), 3000);
    } catch (e) {
      setGenError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-cc-mid border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-sm text-gray-500">Loading job...</p>
        </div>
      </div>
    );
  }

  // Error state
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
        <button
          onClick={() => router.push("/jobs")}
          className="text-sm text-cc-mid hover:underline"
        >
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

          {/* Save status indicator */}
          {saving && (
            <span className="text-xs text-gray-400 flex items-center gap-1">
              <div className="w-1.5 h-1.5 bg-yellow-400 rounded-full animate-pulse" />
              Saving...
            </span>
          )}
          {saveError && (
            <span className="text-xs text-red-500 flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01" />
              </svg>
              Save failed
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Download IM button */}
          {job?.im_filename && (
            <a
              href={getJobImUrl(jobId)}
              className="text-xs text-gray-400 hover:text-cc-mid border border-gray-200 px-3 py-1.5 rounded-lg
                         hover:border-cc-mid/30 transition-all flex items-center gap-1.5"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Download IM
            </a>
          )}

          {/* Deep Research button */}
          <button
            onClick={() => setDeepResearchActive(true)}
            disabled={deepResearchActive}
            className="text-xs text-cc-mid hover:text-cc-dark border border-cc-mid/30 px-3 py-1.5 rounded-lg
                       hover:border-cc-mid/60 transition-all flex items-center gap-1.5 disabled:opacity-50"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
            Run Deep Research
          </button>

          {/* Export JSON button */}
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
      </div>

      {/* Deep Research Progress */}
      {deepResearchActive && (
        <div className="mb-6">
          <DeepResearchProgress
            jobId={jobId}
            onComplete={async () => {
              setDeepResearchActive(false);
              // Reload job to get updated data
              const updatedJob = await getJob(jobId);
              setJob(updatedJob);
              if (updatedJob.edited_data || updatedJob.research_data) {
                const d = updatedJob.edited_data || updatedJob.research_data;
                if (d) setData({ ...EMPTY_ONE_PAGER, ...d });
              }
              setShowDeepResults(true);
            }}
            onError={(msg) => {
              setDeepResearchActive(false);
              setGenError(msg);
            }}
          />
        </div>
      )}

      {/* Deep Research Results */}
      {(showDeepResults || (job?.deep_research_steps && job.deep_research_steps.length > 0)) &&
        job?.deep_research_steps && (
          <div className="mb-6">
            <DeepResearchResults steps={job.deep_research_steps} jobId={jobId} />
          </div>
        )}

      {/* Verification Banner */}
      {verification && <VerificationBanner verification={verification} />}

      {/* 3-column grid matching the slide layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Column 1: Key Facts + Criteria + Status */}
        <div className="space-y-4">
          <HeaderSection
            data={data.header}
            thesis={data.investment_thesis}
            onChange={(header) => updateData({ ...data, header })}
            onThesisChange={(thesis) => updateData({ ...data, investment_thesis: thesis })}
          />
          <KeyFactsSection
            data={data.key_facts}
            onChange={(key_facts) => updateData({ ...data, key_facts })}
          />
          <CriteriaSection
            data={data.investment_criteria}
            onChange={(investment_criteria) => updateData({ ...data, investment_criteria })}
          />
          <MetaSection
            data={data.meta}
            onChange={(meta) => updateData({ ...data, meta })}
          />
        </div>

        {/* Column 2: Description + Portfolio + Revenue Split */}
        <div className="space-y-4">
          <BulletEditor
            title="Description"
            items={data.description}
            onChange={(description) => updateData({ ...data, description })}
          />
          <BulletEditor
            title="Product Portfolio"
            items={data.product_portfolio}
            onChange={(product_portfolio) => updateData({ ...data, product_portfolio })}
          />
          <RevenueTable
            data={data.revenue_split}
            onChange={(revenue_split) => updateData({ ...data, revenue_split })}
          />
        </div>

        {/* Column 3: Rationale + Financials */}
        <div className="space-y-4">
          <RationaleSection
            data={data.investment_rationale}
            onChange={(investment_rationale) => updateData({ ...data, investment_rationale })}
          />
          <FinancialsTable
            data={data.financials}
            onChange={(financials) => updateData({ ...data, financials })}
          />
        </div>
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
            disabled={generating || !data.header.company_name}
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
                Generate One-Pager PPTX
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

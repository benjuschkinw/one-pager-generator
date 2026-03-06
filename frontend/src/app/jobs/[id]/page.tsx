"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { getJob, updateJob, generateJobPptx } from "@/lib/api";
import {
  OnePagerData,
  VerificationResult,
  Job,
  EMPTY_ONE_PAGER,
} from "@/lib/types";

import HeaderSection from "@/app/components/HeaderSection";
import MetaSection from "@/app/components/MetaSection";
import KeyFactsSection from "@/app/components/KeyFactsSection";
import BulletEditor from "@/app/components/BulletEditor";
import RationaleSection from "@/app/components/RationaleSection";
import CriteriaSection from "@/app/components/CriteriaSection";
import RevenueTable from "@/app/components/RevenueTable";
import FinancialsTable from "@/app/components/FinancialsTable";
import VerificationBanner from "@/app/components/VerificationBanner";
import VersionHistory from "@/app/components/VersionHistory";
import NotesPanel from "@/app/components/NotesPanel";

const AUTOSAVE_DELAY = 2000; // 2 seconds

export default function JobDetailPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.id as string;

  const [job, setJob] = useState<Job | null>(null);
  const [data, setData] = useState<OnePagerData>(EMPTY_ONE_PAGER);
  const [verification, setVerification] = useState<VerificationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [generating, setGenerating] = useState(false);

  // Panels
  const [showVersions, setShowVersions] = useState(false);
  const [showNotes, setShowNotes] = useState(false);

  // Track if data has changed for autosave
  const [hasChanges, setHasChanges] = useState(false);
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Load job data
  useEffect(() => {
    async function loadJob() {
      setLoading(true);
      setError(null);

      try {
        const loadedJob = await getJob(jobId);
        setJob(loadedJob);
        setData(loadedJob.edited_data || loadedJob.research_data || EMPTY_ONE_PAGER);
        setVerification(loadedJob.verification);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load job");
      } finally {
        setLoading(false);
      }
    }

    if (jobId) {
      loadJob();
    }
  }, [jobId]);

  // Autosave function
  const saveData = useCallback(async () => {
    if (!job || !hasChanges) return;

    setSaving(true);
    try {
      await updateJob(jobId, { data });
      setLastSaved(new Date());
      setHasChanges(false);
    } catch (e) {
      console.error("Autosave failed:", e);
    } finally {
      setSaving(false);
    }
  }, [job, jobId, data, hasChanges]);

  // Autosave effect
  useEffect(() => {
    if (hasChanges) {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
      saveTimeoutRef.current = setTimeout(saveData, AUTOSAVE_DELAY);
    }

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [hasChanges, saveData]);

  // Track changes to data
  function updateData(newData: OnePagerData) {
    setData(newData);
    setHasChanges(true);
  }

  // Generate PPTX
  async function handleGenerate() {
    // Save any pending changes first
    if (hasChanges) {
      await saveData();
    }

    setGenerating(true);
    try {
      await generateJobPptx(jobId);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  // Handle version restore
  function handleVersionRestore(restoredJob: Job) {
    setJob(restoredJob);
    setData(restoredJob.edited_data || restoredJob.research_data || EMPTY_ONE_PAGER);
    setVerification(restoredJob.verification);
    setHasChanges(false);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin h-8 w-8 border-4 border-cc-mid border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="max-w-lg mx-auto mt-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-700 mb-4">{error || "Job not found"}</p>
          <button
            onClick={() => router.push("/jobs")}
            className="px-4 py-2 bg-cc-dark text-white rounded-lg hover:bg-cc-mid transition-colors"
          >
            Back to Jobs
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push("/jobs")}
            className="text-sm text-gray-500 hover:text-cc-mid transition-colors flex items-center gap-1"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Back to Jobs
          </button>
          <h2 className="text-xl font-bold text-cc-dark">
            {data.header.company_name || "New One-Pager"}
          </h2>

          {/* Save status */}
          <span className="text-sm text-gray-400">
            {saving ? (
              "Saving..."
            ) : lastSaved ? (
              `Saved ${lastSaved.toLocaleTimeString()}`
            ) : hasChanges ? (
              "Unsaved changes"
            ) : (
              ""
            )}
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Version History */}
          <button
            onClick={() => setShowVersions(!showVersions)}
            className={`px-3 py-1.5 text-sm border rounded transition-colors ${
              showVersions
                ? "bg-cc-mid text-white border-cc-mid"
                : "border-gray-300 hover:bg-gray-50"
            }`}
          >
            History
          </button>

          {/* Notes */}
          <button
            onClick={() => setShowNotes(!showNotes)}
            className={`px-3 py-1.5 text-sm border rounded transition-colors ${
              showNotes
                ? "bg-cc-mid text-white border-cc-mid"
                : "border-gray-300 hover:bg-gray-50"
            }`}
          >
            Notes
          </button>

          {/* Export JSON */}
          <button
            onClick={() => {
              const blob = new Blob([JSON.stringify(data, null, 2)], {
                type: "application/json",
              });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `${data.header.company_name || "one_pager"}_data.json`;
              a.click();
              URL.revokeObjectURL(url);
            }}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50"
          >
            Export JSON
          </button>

          {/* Generate PPTX */}
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-4 py-2 bg-cc-dark text-white rounded-lg hover:bg-cc-mid transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {generating ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                Generating...
              </>
            ) : (
              <>
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                Generate PPTX
              </>
            )}
          </button>
        </div>
      </div>

      {/* Verification Banner */}
      {verification && <VerificationBanner verification={verification} />}

      {/* Main Content with Sidebars */}
      <div className="flex gap-4">
        {/* Editor Grid */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Column 1: Key Facts + Criteria + Status */}
          <div className="space-y-4">
            <HeaderSection
              data={data.header}
              thesis={data.investment_thesis}
              onChange={(header) => updateData({ ...data, header })}
              onThesisChange={(thesis) =>
                updateData({ ...data, investment_thesis: thesis })
              }
            />
            <KeyFactsSection
              data={data.key_facts}
              onChange={(key_facts) => updateData({ ...data, key_facts })}
            />
            <CriteriaSection
              data={data.investment_criteria}
              onChange={(investment_criteria) =>
                updateData({ ...data, investment_criteria })
              }
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
              onChange={(product_portfolio) =>
                updateData({ ...data, product_portfolio })
              }
            />
            <RevenueTable
              data={data.revenue_split}
              onChange={(revenue_split) =>
                updateData({ ...data, revenue_split })
              }
            />
          </div>

          {/* Column 3: Rationale + Financials */}
          <div className="space-y-4">
            <RationaleSection
              data={data.investment_rationale}
              onChange={(investment_rationale) =>
                updateData({ ...data, investment_rationale })
              }
            />
            <FinancialsTable
              data={data.financials}
              onChange={(financials) => updateData({ ...data, financials })}
            />
          </div>
        </div>

        {/* Version History Sidebar */}
        {showVersions && (
          <div className="w-80 flex-shrink-0">
            <VersionHistory jobId={jobId} onRestore={handleVersionRestore} />
          </div>
        )}

        {/* Notes Sidebar */}
        {showNotes && (
          <div className="w-80 flex-shrink-0">
            <NotesPanel jobId={jobId} />
          </div>
        )}
      </div>
    </div>
  );
}

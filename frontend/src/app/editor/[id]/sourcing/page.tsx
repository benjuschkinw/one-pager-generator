"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { CompanySourcingResult, CompanyProfile, Job, DeepResearchSSEEvent } from "@/lib/types";
import { getJob, startCompanySourcing, saveSourcingData } from "@/lib/api";

interface StepState {
  name: string;
  label: string;
  status: "pending" | "running" | "done" | "error";
  model?: string;
  duration?: number;
  message?: string;
}

const SOURCING_STEPS = [
  { name: "extract_dna", label: "Extract Company DNA" },
  { name: "search_dach", label: "Search DACH Companies" },
  { name: "verify_enrich", label: "Verify & Enrich" },
  { name: "rank_synthesize", label: "Rank & Synthesize" },
];

function CompanyCard({
  company,
  expanded,
  onToggle,
}: {
  company: CompanyProfile;
  expanded: boolean;
  onToggle: () => void;
}) {
  const scoreColor =
    company.similarity_score >= 80
      ? "text-green-700 bg-green-100"
      : company.similarity_score >= 60
      ? "text-yellow-700 bg-yellow-100"
      : "text-red-700 bg-red-100";

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50/50 transition-colors text-left"
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className={`text-xs font-bold px-2 py-1 rounded ${scoreColor}`}>
            {Math.round(company.similarity_score)}%
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-cc-dark truncate">
                {company.name}
              </span>
              <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">
                {company.hq_country}
              </span>
            </div>
            <p className="text-xs text-gray-400 truncate">
              {company.hq_city}
              {company.industry && ` · ${company.industry}`}
              {company.ownership_type && ` · ${company.ownership_type}`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4 flex-shrink-0">
          {company.revenue_eur_m != null && (
            <div className="text-right">
              <p className="text-xs text-gray-500">Revenue</p>
              <p className="text-sm font-medium text-cc-dark">
                {company.revenue_estimate ? "~" : ""}EUR {company.revenue_eur_m}M
              </p>
            </div>
          )}
          {company.employee_count != null && (
            <div className="text-right">
              <p className="text-xs text-gray-500">Employees</p>
              <p className="text-sm font-medium text-cc-dark">
                {company.employee_estimate ? "~" : ""}{company.employee_count}
              </p>
            </div>
          )}
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform ${expanded ? "rotate-180" : ""}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-gray-100 pt-3">
          {/* Description */}
          {company.description && (
            <p className="text-sm text-gray-600">{company.description}</p>
          )}

          {/* Details grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {company.website && (
              <div>
                <p className="text-[10px] text-gray-400 uppercase">Website</p>
                <a
                  href={company.website.startsWith("http") ? company.website : `https://${company.website}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-cc-mid hover:underline truncate block"
                >
                  {company.website.replace(/^https?:\/\/(www\.)?/, "")}
                </a>
              </div>
            )}
            {company.founded_year && (
              <div>
                <p className="text-[10px] text-gray-400 uppercase">Founded</p>
                <p className="text-xs text-cc-dark">{company.founded_year}</p>
              </div>
            )}
            {company.business_model && (
              <div>
                <p className="text-[10px] text-gray-400 uppercase">Business Model</p>
                <p className="text-xs text-cc-dark">{company.business_model}</p>
              </div>
            )}
            {company.ebitda_margin_pct != null && (
              <div>
                <p className="text-[10px] text-gray-400 uppercase">EBITDA Margin</p>
                <p className="text-xs text-cc-dark">{company.ebitda_margin_pct}%</p>
              </div>
            )}
            {company.sub_sector && (
              <div>
                <p className="text-[10px] text-gray-400 uppercase">Sub-Sector</p>
                <p className="text-xs text-cc-dark">{company.sub_sector}</p>
              </div>
            )}
          </div>

          {/* Similarity dimensions */}
          {Object.keys(company.similarity_dimensions).length > 0 && (
            <div>
              <p className="text-[10px] text-gray-400 uppercase mb-1">Similarity Breakdown</p>
              <div className="flex flex-wrap gap-1">
                {Object.entries(company.similarity_dimensions).map(([dim, score]) => (
                  <span
                    key={dim}
                    className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded"
                  >
                    {dim}: {Math.round(score)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Similarity rationale */}
          {company.similarity_rationale && (
            <div>
              <p className="text-[10px] text-gray-400 uppercase mb-1">Why Similar</p>
              <p className="text-xs text-gray-600">{company.similarity_rationale}</p>
            </div>
          )}

          {/* Products/Services */}
          {company.key_products_services.length > 0 && (
            <div>
              <p className="text-[10px] text-gray-400 uppercase mb-1">Products & Services</p>
              <div className="flex flex-wrap gap-1">
                {company.key_products_services.map((p, i) => (
                  <span key={i} className="text-[10px] px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded">
                    {p}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Data sources */}
          {company.data_sources.length > 0 && (
            <div>
              <p className="text-[10px] text-gray-400 uppercase mb-1">Sources</p>
              <div className="flex flex-wrap gap-1">
                {company.data_sources.map((src, i) => (
                  <span key={i} className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">
                    {src}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Confidence */}
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <span>
              Confidence:{" "}
              <span className={`font-medium ${
                company.confidence >= 0.8 ? "text-green-700" :
                company.confidence >= 0.5 ? "text-yellow-700" : "text-red-700"
              }`}>
                {Math.round(company.confidence * 100)}%
              </span>
            </span>
            {company.data_freshness && <span>· Data: {company.data_freshness}</span>}
          </div>

          {/* Future: deep research button placeholder */}
          <div className="pt-2 border-t border-gray-100">
            <button
              disabled
              className="text-xs text-gray-400 border border-gray-200 px-3 py-1.5 rounded-lg
                         cursor-not-allowed opacity-50 flex items-center gap-1.5"
              title="Coming soon: Deep research and premium API verification"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
              Deep Research (coming soon)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function SourcingPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;

  const [job, setJob] = useState<Job | null>(null);
  const [sourcingData, setSourcingData] = useState<CompanySourcingResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedCompany, setExpandedCompany] = useState<string | null>(null);

  // SSE progress state
  const [sourcingActive, setSourcingActive] = useState(false);
  const [steps, setSteps] = useState<StepState[]>(
    SOURCING_STEPS.map((s) => ({ ...s, status: "pending" as const }))
  );
  const [completed, setCompleted] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);
  const completedRef = useRef(false);

  const loadJob = useCallback(async () => {
    try {
      setLoading(true);
      const jobData = await getJob(jobId);
      setJob(jobData);
      const data = jobData.edited_sourcing_data || jobData.sourcing_data;
      if (data) {
        setSourcingData(data);
      } else {
        // No sourcing data yet — start sourcing
        setSourcingActive(true);
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

  // Start sourcing SSE
  useEffect(() => {
    if (!sourcingActive) return;

    const controller = startCompanySourcing(
      jobId,
      (event: string, data: DeepResearchSSEEvent) => {
        if (completedRef.current) return;
        setSteps((prev) => {
          const updated = [...prev];
          const idx = updated.findIndex((s) => s.name === data.step);
          if (idx === -1) return prev;
          updated[idx] = {
            ...updated[idx],
            status: (data.status as StepState["status"]) || updated[idx].status,
            model: data.model || updated[idx].model,
            duration: data.duration ?? updated[idx].duration,
            message: data.message || updated[idx].message,
          };
          return updated;
        });
      },
      async () => {
        if (completedRef.current) return;
        completedRef.current = true;
        setCompleted(true);
        setSourcingActive(false);
        // Reload to get results
        const updatedJob = await getJob(jobId);
        setJob(updatedJob);
        const data = updatedJob.edited_sourcing_data || updatedJob.sourcing_data;
        if (data) setSourcingData(data);
      },
      (err: string) => {
        if (completedRef.current) return;
        completedRef.current = true;
        setErrorMsg(err);
        setSourcingActive(false);
      },
    );

    controllerRef.current = controller;
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sourcingActive, jobId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-cc-mid border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-sm text-gray-500">Loading sourcing data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-lg mx-auto mt-16 text-center">
        <h2 className="text-lg font-semibold text-cc-dark mb-2">Error</h2>
        <p className="text-sm text-gray-500 mb-6">{error}</p>
        <button onClick={() => router.push(`/editor/${jobId}`)} className="text-sm text-cc-mid hover:underline">
          Back to One-Pager
        </button>
      </div>
    );
  }

  const doneCount = steps.filter((s) => s.status === "done").length;
  const runningCount = steps.filter((s) => s.status === "running").length;

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push(`/editor/${jobId}`)}
            className="text-xs text-gray-400 hover:text-cc-mid transition-colors flex items-center gap-1"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to One-Pager
          </button>
          <div className="h-4 w-px bg-gray-200" />
          <div>
            <h2 className="text-lg font-semibold text-cc-dark">
              Company Sourcing: {job?.company_name || ""}
            </h2>
            {sourcingData && (
              <p className="text-xs text-gray-400">
                {sourcingData.seed_industry && `${sourcingData.seed_industry} · `}
                {sourcingData.seed_revenue_range && `${sourcingData.seed_revenue_range} · `}
                {sourcingData.search_region}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Progress (when sourcing is active or just completed) */}
      {(sourcingActive || (completed && !sourcingData)) && (
        <div className="mb-6 bg-white rounded-xl shadow-sm border border-gray-200/80 overflow-hidden">
          <div className="px-6 pt-6 pb-4 border-b border-gray-100">
            <h3 className="text-sm font-semibold text-cc-dark">Sourcing Progress</h3>
            <div className="mt-3 h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  errorMsg ? "bg-red-400" : completed ? "bg-green-500" : "bg-cc-mid"
                }`}
                style={{ width: `${((doneCount + runningCount * 0.5) / steps.length) * 100}%` }}
              />
            </div>
          </div>
          <div className="px-6 py-4 space-y-3">
            {steps.map((step) => (
              <div key={step.name} className="flex items-center gap-3">
                {step.status === "done" ? (
                  <div className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                ) : step.status === "running" ? (
                  <div className="w-5 h-5 rounded-full border-2 border-blue-400 bg-blue-50 flex items-center justify-center">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                  </div>
                ) : step.status === "error" ? (
                  <div className="w-5 h-5 rounded-full bg-red-500 flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </div>
                ) : (
                  <div className="w-5 h-5 rounded-full border-2 border-gray-300 bg-white" />
                )}
                <span className={`text-sm ${step.status === "pending" ? "text-gray-400" : "text-cc-dark"}`}>
                  {step.label}
                </span>
                {step.duration != null && (
                  <span className="text-[10px] text-gray-400">{step.duration.toFixed(1)}s</span>
                )}
                {step.message && step.status === "done" && (
                  <span className="text-[10px] text-gray-400">{step.message}</span>
                )}
              </div>
            ))}
          </div>
          {errorMsg && (
            <div className="px-6 py-3 bg-red-50 border-t border-red-200">
              <p className="text-sm text-red-700">{errorMsg}</p>
            </div>
          )}
        </div>
      )}

      {/* Results */}
      {sourcingData && (
        <>
          {/* Executive Summary */}
          {sourcingData.executive_summary && (
            <div className="mb-4 bg-white rounded-xl shadow-sm border border-gray-200/80 p-6">
              <h3 className="text-sm font-semibold text-cc-dark mb-2">Executive Summary</h3>
              <p className="text-sm text-gray-600">{sourcingData.executive_summary}</p>
            </div>
          )}

          {/* Summary Stats */}
          {sourcingData.summary.count > 0 && (
            <div className="mb-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200/80 p-4 text-center">
                <p className="text-2xl font-bold text-cc-dark">{sourcingData.summary.count}</p>
                <p className="text-xs text-gray-500">Companies</p>
              </div>
              {sourcingData.summary.avg_revenue_eur_m != null && (
                <div className="bg-white rounded-xl shadow-sm border border-gray-200/80 p-4 text-center">
                  <p className="text-2xl font-bold text-cc-dark">
                    EUR {sourcingData.summary.avg_revenue_eur_m.toFixed(1)}M
                  </p>
                  <p className="text-xs text-gray-500">Avg Revenue</p>
                </div>
              )}
              {sourcingData.summary.avg_ebitda_margin != null && (
                <div className="bg-white rounded-xl shadow-sm border border-gray-200/80 p-4 text-center">
                  <p className="text-2xl font-bold text-cc-dark">
                    {sourcingData.summary.avg_ebitda_margin.toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-500">Avg EBITDA Margin</p>
                </div>
              )}
              {sourcingData.summary.avg_employees != null && (
                <div className="bg-white rounded-xl shadow-sm border border-gray-200/80 p-4 text-center">
                  <p className="text-2xl font-bold text-cc-dark">{sourcingData.summary.avg_employees}</p>
                  <p className="text-xs text-gray-500">Avg Employees</p>
                </div>
              )}
            </div>
          )}

          {/* Country Distribution */}
          {Object.keys(sourcingData.summary.country_distribution).length > 0 && (
            <div className="mb-4 flex gap-2">
              {Object.entries(sourcingData.summary.country_distribution).map(([country, count]) => (
                <span
                  key={country}
                  className="text-xs px-2 py-1 bg-white rounded-lg shadow-sm border border-gray-200/80"
                >
                  {country}: {count}
                </span>
              ))}
              {Object.entries(sourcingData.summary.ownership_distribution).map(([type, count]) => (
                <span
                  key={type}
                  className="text-xs px-2 py-1 bg-white rounded-lg shadow-sm border border-gray-200/80"
                >
                  {type}: {count}
                </span>
              ))}
            </div>
          )}

          {/* Company List with Drill-Down */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200/80 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-cc-dark">
                Comparable Companies ({sourcingData.companies.length})
              </h3>
              {/* Comp Table header */}
              <div className="flex items-center gap-2 text-[10px] text-gray-400">
                <span>Sorted by similarity</span>
              </div>
            </div>

            <div className="divide-y divide-gray-100">
              {sourcingData.companies
                .sort((a, b) => b.similarity_score - a.similarity_score)
                .map((company) => (
                  <CompanyCard
                    key={company.name}
                    company={company}
                    expanded={expandedCompany === company.name}
                    onToggle={() =>
                      setExpandedCompany(
                        expandedCompany === company.name ? null : company.name
                      )
                    }
                  />
                ))}
            </div>

            {sourcingData.companies.length === 0 && (
              <div className="px-6 py-12 text-center">
                <p className="text-sm text-gray-500">No comparable companies found.</p>
              </div>
            )}
          </div>

          {/* Export JSON */}
          <div className="mt-4 flex items-center gap-2">
            <button
              onClick={() => {
                const blob = new Blob([JSON.stringify(sourcingData, null, 2)], { type: "application/json" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `Sourcing_${(job?.company_name || "export").replace(/[^a-zA-Z0-9_\- ]/g, "_").substring(0, 100)}.json`;
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
        </>
      )}
    </div>
  );
}

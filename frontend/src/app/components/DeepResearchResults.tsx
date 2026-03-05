"use client";

import { useState } from "react";
import { DeepResearchStep } from "@/lib/types";

interface DeepResearchResultsProps {
  steps: DeepResearchStep[];
  jobId: string;
}

function StatusBadge({ status }: { status: DeepResearchStep["status"] }) {
  switch (status) {
    case "verified":
      return (
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-100 text-green-700 font-medium">
          verified
        </span>
      );
    case "done":
      return (
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-medium">
          done
        </span>
      );
    case "error":
      return (
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-100 text-red-700 font-medium">
          error
        </span>
      );
    case "running":
      return (
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-yellow-100 text-yellow-700 font-medium">
          running
        </span>
      );
    default:
      return (
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 font-medium">
          {status}
        </span>
      );
  }
}

function HallucinationBadge({ risk }: { risk: "low" | "medium" | "high" }) {
  switch (risk) {
    case "low":
      return (
        <span className="text-[10px] px-1.5 py-0.5 rounded font-medium bg-green-100 text-green-700">
          Low Risk
        </span>
      );
    case "medium":
      return (
        <span className="text-[10px] px-1.5 py-0.5 rounded font-medium bg-yellow-100 text-yellow-700">
          Medium Risk
        </span>
      );
    case "high":
      return (
        <span className="text-[10px] px-1.5 py-0.5 rounded font-medium bg-red-100 text-red-700">
          High Risk
        </span>
      );
  }
}

function formatDuration(startedAt: string | null, completedAt: string | null): string | null {
  if (!startedAt || !completedAt) return null;
  const ms = new Date(completedAt).getTime() - new Date(startedAt).getTime();
  return `${(ms / 1000).toFixed(1)}s`;
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return "text-green-700";
  if (confidence >= 0.5) return "text-yellow-700";
  return "text-red-700";
}

function StepCard({ step }: { step: DeepResearchStep }) {
  const [showRaw, setShowRaw] = useState(false);

  const duration = formatDuration(step.started_at, step.completed_at);

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Step header */}
      <div className="px-4 py-3 bg-gray-50 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-cc-dark">{step.label}</span>
          <StatusBadge status={step.status} />
          {step.verification?.confidence != null && (
            <span
              className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                step.verification.confidence >= 0.8
                  ? "bg-green-100 text-green-700"
                  : step.verification.confidence >= 0.5
                  ? "bg-yellow-100 text-yellow-700"
                  : "bg-red-100 text-red-700"
              }`}
            >
              {Math.round(step.verification.confidence * 100)}% conf
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 text-[10px] text-gray-400">
          {step.model_used && (
            <span className="px-1.5 py-0.5 bg-gray-100 rounded font-mono">
              {step.model_used}
            </span>
          )}
          {duration && <span>{duration}</span>}
          {step.result_json && (
            <span>{Object.keys(step.result_json).length} fields</span>
          )}
        </div>
      </div>

      {/* Step body */}
      <div className="px-4 py-3 space-y-2">
        {/* Verification details */}
        {step.verification && (
          <div className="p-3 bg-cc-surface rounded-lg space-y-2">
            <h4 className="text-xs font-semibold text-cc-dark uppercase tracking-wide">
              Verification
            </h4>
            <div className="flex items-center gap-3 flex-wrap text-xs">
              <span className="text-gray-500">
                Verifier:{" "}
                <span className="font-mono text-gray-700">
                  {step.verification.verifier_model}
                </span>
              </span>
              <span className="text-gray-500">
                Confidence:{" "}
                <span
                  className={`font-medium ${getConfidenceColor(step.verification.confidence)}`}
                >
                  {Math.round(step.verification.confidence * 100)}%
                </span>
              </span>
              {step.verification.hallucination_risk && (
                <span className="text-gray-500">
                  Hallucination: <HallucinationBadge risk={step.verification.hallucination_risk} />
                </span>
              )}
            </div>

            {/* Verification flags */}
            {step.verification.flags.length > 0 && (
              <div className="mt-2 space-y-1">
                {step.verification.flags.map((flag, i) => {
                  let flagClass: string;
                  if (flag.severity === "error")
                    flagClass = "bg-red-50 border-red-200 text-red-700";
                  else if (flag.severity === "warning")
                    flagClass = "bg-yellow-50 border-yellow-200 text-yellow-700";
                  else flagClass = "bg-blue-50 border-blue-200 text-blue-700";

                  return (
                    <div
                      key={i}
                      className={`rounded border p-1.5 text-[10px] ${flagClass}`}
                    >
                      <span className="font-mono opacity-70">{flag.field}</span>:{" "}
                      {flag.message}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Error message */}
        {step.error_message && (
          <p className="text-xs text-red-600">{step.error_message}</p>
        )}

        {/* Sources */}
        {step.sources && step.sources.length > 0 && (
          <div className="p-3 bg-cc-surface rounded-lg space-y-1.5">
            <h4 className="text-xs font-semibold text-cc-dark uppercase tracking-wide">
              Sources
            </h4>
            <div className="flex flex-wrap gap-1">
              {step.sources.map((src, i) => {
                let validUrl: URL | null = null;
                try { if (src.startsWith("http")) validUrl = new URL(src); } catch { /* invalid */ }
                return (
                  <a
                    key={i}
                    href={validUrl ? src : undefined}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`text-[10px] px-1.5 py-0.5 rounded bg-gray-100 ${
                      validUrl
                        ? "text-cc-mid hover:bg-cc-surface cursor-pointer"
                        : "text-gray-500"
                    } truncate max-w-[200px]`}
                  >
                    {validUrl
                      ? validUrl.hostname.replace("www.", "")
                      : src}
                  </a>
                );
              })}
            </div>
          </div>
        )}

        {/* Raw JSON toggle */}
        {step.result_json && (
          <div>
            <button
              onClick={() => setShowRaw(!showRaw)}
              className="text-[10px] text-gray-400 hover:text-cc-mid transition-colors"
            >
              {showRaw ? "Hide raw output" : "Show raw output"}
            </button>
            {showRaw && (
              <pre className="mt-1 p-2 bg-gray-900 text-gray-100 rounded text-[10px] font-mono overflow-x-auto max-h-48 overflow-y-auto leading-relaxed">
                {JSON.stringify(step.result_json, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function DeepResearchResults({ steps, jobId }: DeepResearchResultsProps) {
  const [collapsed, setCollapsed] = useState(false);

  if (!steps || steps.length === 0) return null;

  // Compute summary stats
  const completedSteps = steps.filter(
    (s) => s.status === "done" || s.status === "verified"
  );
  const confidences = steps
    .map((s) => s.verification?.confidence)
    .filter((c): c is number => c != null);
  const avgConfidence =
    confidences.length > 0
      ? confidences.reduce((a, b) => a + b, 0) / confidences.length
      : null;
  const confidencePct = avgConfidence != null ? Math.round(avgConfidence * 100) : null;

  let totalDurationMs = 0;
  for (const step of steps) {
    if (step.started_at && step.completed_at) {
      totalDurationMs +=
        new Date(step.completed_at).getTime() - new Date(step.started_at).getTime();
    }
  }
  const totalDuration =
    totalDurationMs > 0 ? `${(totalDurationMs / 1000).toFixed(1)}s` : null;

  const hasErrors = steps.some((s) => s.status === "error");
  const hasWarnings = steps.some(
    (s) =>
      s.verification?.flags.some((f) => f.severity === "warning") ||
      (s.verification?.confidence != null && s.verification.confidence < 0.8)
  );

  let bannerClass: string;
  if (hasErrors) {
    bannerClass = "bg-red-50 border-red-200";
  } else if (hasWarnings) {
    bannerClass = "bg-yellow-50 border-yellow-200";
  } else {
    bannerClass = "bg-green-50 border-green-200";
  }

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-200/80 overflow-hidden`}>
      {/* Header with collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className={`w-full px-6 pt-5 pb-4 border-b border-gray-100 flex items-center justify-between text-left hover:bg-gray-50/50 transition-colors`}
      >
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-cc-dark">Deep Research Results</h3>
            <span className="text-[10px] px-1.5 py-0.5 bg-cc-surface text-cc-mid rounded font-medium">
              {jobId.slice(0, 8)}
            </span>
            {/* Overall status indicator */}
            {hasErrors ? (
              <span className="text-[10px] px-1.5 py-0.5 bg-red-100 text-red-700 rounded font-medium">
                Errors
              </span>
            ) : hasWarnings ? (
              <span className="text-[10px] px-1.5 py-0.5 bg-yellow-100 text-yellow-700 rounded font-medium">
                Warnings
              </span>
            ) : (
              <span className="text-[10px] px-1.5 py-0.5 bg-green-100 text-green-700 rounded font-medium">
                Passed
              </span>
            )}
          </div>
          {/* Summary stats */}
          <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-500">
            <span>
              {completedSteps.length}/{steps.length} steps completed
            </span>
            {confidencePct != null && (
              <>
                <span className="text-gray-300">|</span>
                <span>
                  Avg confidence:{" "}
                  <span
                    className={`font-medium ${getConfidenceColor(avgConfidence!)}`}
                  >
                    {confidencePct}%
                  </span>
                </span>
              </>
            )}
            {totalDuration && (
              <>
                <span className="text-gray-300">|</span>
                <span>Total: {totalDuration}</span>
              </>
            )}
          </div>
        </div>
        <svg
          className={`w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ${
            collapsed ? "" : "rotate-180"
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Steps list */}
      {!collapsed && (
        <div className="p-6 space-y-3">
          {steps.map((step) => (
            <StepCard key={step.step_name} step={step} />
          ))}
        </div>
      )}
    </div>
  );
}

"use client";

import { useState, useEffect, useRef } from "react";
import { startDeepResearch } from "@/lib/api";
import { DeepResearchSSEEvent } from "@/lib/types";

interface DeepResearchProgressProps {
  jobId: string;
  onComplete: () => void;
  onError: (message: string) => void;
}

interface StepState {
  name: string;
  label: string;
  status: "pending" | "running" | "done" | "error" | "verified";
  model?: string;
  duration?: number;
  confidence?: number;
  message?: string;
}

const DEEP_STEPS = [
  { name: "im_extraction", label: "IM Extraction" },
  { name: "web_research", label: "Web Research" },
  { name: "financials", label: "Financial Deep-Dive" },
  { name: "management", label: "Management & Org" },
  { name: "market", label: "Market & Competitive" },
  { name: "merge", label: "Merge & Synthesize" },
  { name: "verify_final", label: "Cross-Verify" },
];

export default function DeepResearchProgress({
  jobId,
  onComplete,
  onError,
}: DeepResearchProgressProps) {
  const [steps, setSteps] = useState<StepState[]>(
    DEEP_STEPS.map((s) => ({ ...s, status: "pending" }))
  );
  const [completed, setCompleted] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);
  const completedRef = useRef(false);

  useEffect(() => {
    const controller = startDeepResearch(
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
            confidence: data.confidence ?? updated[idx].confidence,
            message: data.message || updated[idx].message,
          };

          return updated;
        });

        if (event === "error") {
          setErrorMsg(data.message || "Deep research failed");
        }
      },
      () => {
        if (completedRef.current) return;
        completedRef.current = true;
        setCompleted(true);
        onComplete();
      },
      (error: string) => {
        if (completedRef.current) return;
        completedRef.current = true;
        setErrorMsg(error);
        onError(error);
      }
    );

    controllerRef.current = controller;

    return () => {
      controller.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  function getStatusIcon(status: StepState["status"]) {
    switch (status) {
      case "pending":
        return (
          <div className="w-6 h-6 rounded-full border-2 border-gray-300 bg-white flex items-center justify-center flex-shrink-0">
            <div className="w-2 h-2 rounded-full bg-gray-300" />
          </div>
        );
      case "running":
        return (
          <div className="w-6 h-6 rounded-full border-2 border-blue-400 bg-blue-50 flex items-center justify-center flex-shrink-0">
            <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          </div>
        );
      case "done":
      case "verified":
        return (
          <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0">
            <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        );
      case "error":
        return (
          <div className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center flex-shrink-0">
            <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        );
    }
  }

  const runningCount = steps.filter((s) => s.status === "running").length;
  const doneCount = steps.filter((s) => s.status === "done" || s.status === "verified").length;
  const totalSteps = steps.length;

  return (
    <div className="max-w-lg mx-auto">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200/80 overflow-hidden">
        {/* Header */}
        <div className="px-6 pt-6 pb-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-cc-dark">Deep Research</h2>
          <p className="text-sm text-gray-500 mt-1">
            {completed
              ? "Research complete"
              : errorMsg
              ? "Research encountered an error"
              : `Running multi-step AI analysis... (${doneCount}/${totalSteps})`}
          </p>
          {/* Progress bar */}
          <div className="mt-3 h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                errorMsg ? "bg-red-400" : completed ? "bg-green-500" : "bg-cc-mid"
              }`}
              style={{ width: `${((doneCount + runningCount * 0.5) / totalSteps) * 100}%` }}
            />
          </div>
        </div>

        {/* Steps */}
        <div className="px-6 py-4">
          <div className="space-y-0">
            {steps.map((step, i) => (
              <div key={step.name} className="flex items-start gap-3 relative">
                {/* Vertical connector line */}
                {i < steps.length - 1 && (
                  <div
                    className={`absolute left-3 top-6 w-px h-full -translate-x-1/2 ${
                      step.status === "done" || step.status === "verified"
                        ? "bg-green-300"
                        : "bg-gray-200"
                    }`}
                  />
                )}

                {/* Status icon */}
                {getStatusIcon(step.status)}

                {/* Step content */}
                <div className="flex-1 pb-5 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className={`text-sm font-medium ${
                        step.status === "pending"
                          ? "text-gray-400"
                          : step.status === "error"
                          ? "text-red-700"
                          : "text-cc-dark"
                      }`}
                    >
                      {step.label}
                    </span>

                    {/* Model badge */}
                    {step.model && (
                      <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded font-mono">
                        {step.model}
                      </span>
                    )}

                    {/* Duration */}
                    {step.duration != null && (
                      <span className="text-[10px] text-gray-400">
                        {step.duration.toFixed(1)}s
                      </span>
                    )}

                    {/* Confidence */}
                    {step.confidence != null && (
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                          step.confidence >= 0.8
                            ? "bg-green-100 text-green-700"
                            : step.confidence >= 0.5
                            ? "bg-yellow-100 text-yellow-700"
                            : "bg-red-100 text-red-700"
                        }`}
                      >
                        {Math.round(step.confidence * 100)}%
                      </span>
                    )}
                  </div>

                  {/* Error message */}
                  {step.status === "error" && step.message && (
                    <p className="text-xs text-red-600 mt-1">{step.message}</p>
                  )}

                  {/* Running indicator text */}
                  {step.status === "running" && (
                    <p className="text-xs text-blue-500 mt-1 animate-pulse">Processing...</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Error footer */}
        {errorMsg && !completed && (
          <div className="px-6 py-3 bg-red-50 border-t border-red-200">
            <p className="text-sm text-red-700">{errorMsg}</p>
          </div>
        )}

        {/* Complete footer */}
        {completed && (
          <div className="px-6 py-3 bg-green-50 border-t border-green-200">
            <p className="text-sm text-green-700 font-medium">
              All steps complete. Loading results...
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import { VerificationResult } from "@/lib/types";

interface VerificationBannerProps {
  verification: VerificationResult;
}

export default function VerificationBanner({ verification }: VerificationBannerProps) {
  const [expanded, setExpanded] = useState(false);

  const errorCount = verification.flags.filter((f) => f.severity === "error").length;
  const warningCount = verification.flags.filter((f) => f.severity === "warning").length;
  const infoCount = verification.flags.filter((f) => f.severity === "info").length;

  const confidencePct = Math.round(verification.confidence * 100);

  // Choose banner style based on verification result
  let bannerClass: string;
  let icon: string;
  let title: string;

  if (verification.verified && errorCount === 0) {
    bannerClass = "bg-green-50 border-green-200 text-green-800";
    icon = "✓";
    title = `Verified (${confidencePct}% confidence)`;
  } else if (errorCount > 0) {
    bannerClass = "bg-red-50 border-red-200 text-red-800";
    icon = "✗";
    title = `Issues found (${confidencePct}% confidence)`;
  } else {
    bannerClass = "bg-yellow-50 border-yellow-200 text-yellow-800";
    icon = "!";
    title = `Warnings (${confidencePct}% confidence)`;
  }

  if (verification.flags.length === 0) {
    return (
      <div className={`rounded-lg border p-3 mb-4 ${bannerClass}`}>
        <div className="flex items-center gap-2 text-sm font-medium">
          <span className="text-lg">{icon}</span>
          <span>{title} — No issues detected</span>
          {verification.verifier_model && (
            <span className="ml-auto text-xs opacity-60">
              Verified by {verification.verifier_model}
            </span>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-lg border p-3 mb-4 ${bannerClass}`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between text-sm font-medium"
      >
        <div className="flex items-center gap-2">
          <span className="text-lg">{icon}</span>
          <span>{title}</span>
          <span className="flex gap-2 ml-2">
            {errorCount > 0 && (
              <span className="bg-red-100 text-red-700 px-1.5 py-0.5 rounded text-xs">
                {errorCount} error{errorCount > 1 ? "s" : ""}
              </span>
            )}
            {warningCount > 0 && (
              <span className="bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded text-xs">
                {warningCount} warning{warningCount > 1 ? "s" : ""}
              </span>
            )}
            {infoCount > 0 && (
              <span className="bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded text-xs">
                {infoCount} info
              </span>
            )}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {verification.verifier_model && (
            <span className="text-xs opacity-60">
              {verification.verifier_model}
            </span>
          )}
          <svg
            className={`w-4 h-4 transition-transform ${expanded ? "rotate-180" : ""}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="mt-3 space-y-2">
          {verification.flags.map((flag, i) => {
            let flagClass: string;
            let flagIcon: string;
            if (flag.severity === "error") {
              flagClass = "bg-red-100 border-red-200";
              flagIcon = "✗";
            } else if (flag.severity === "warning") {
              flagClass = "bg-yellow-100 border-yellow-200";
              flagIcon = "!";
            } else {
              flagClass = "bg-blue-100 border-blue-200";
              flagIcon = "i";
            }

            return (
              <div key={i} className={`rounded border p-2 text-xs ${flagClass}`}>
                <div className="flex items-start gap-2">
                  <span className="font-bold w-4 text-center flex-shrink-0">{flagIcon}</span>
                  <div>
                    <span className="font-mono text-[10px] opacity-70">{flag.field}</span>
                    <p className="mt-0.5">{flag.message}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

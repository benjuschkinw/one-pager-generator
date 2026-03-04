"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Legacy editor page.
 * All editing now goes through /editor/[id] with job persistence.
 * This page redirects to /jobs or loads sessionStorage data as a fallback.
 */
export default function LegacyEditorPage() {
  const router = useRouter();

  useEffect(() => {
    // Check if there's data in sessionStorage (from old flow or manual editor)
    const stored = sessionStorage.getItem("onePagerData");
    if (!stored) {
      // No data — redirect to jobs page
      router.replace("/jobs");
    }
    // If there is data, show the "select a job" message below
  }, [router]);

  // Check client-side if sessionStorage has data
  const hasData = typeof window !== "undefined" && sessionStorage.getItem("onePagerData");

  if (!hasData) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-cc-mid border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-sm text-gray-500">Redirecting...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto mt-20">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200/80 p-8 text-center">
        <div className="w-12 h-12 rounded-full bg-cc-surface flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h2 className="text-lg font-semibold text-cc-dark mb-2">Select a Job</h2>
        <p className="text-sm text-gray-500 mb-6">
          Research jobs are now saved automatically. Select a job from the history to continue editing, or start a new research.
        </p>
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => router.push("/jobs")}
            className="px-4 py-2 bg-cc-dark text-white rounded-lg text-sm font-medium hover:bg-cc-mid transition-colors"
          >
            View Jobs
          </button>
          <button
            onClick={() => router.push("/")}
            className="px-4 py-2 border border-gray-200 text-gray-600 rounded-lg text-sm font-medium hover:border-cc-mid/30 transition-colors"
          >
            New Research
          </button>
        </div>
      </div>
    </div>
  );
}

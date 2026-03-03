"use client";

import { useState } from "react";
import { OnePagerData } from "@/lib/types";
import { generatePptx } from "@/lib/api";

interface Props {
  data: OnePagerData;
}

export default function GenerateButton({ data }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      await generatePptx(data);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="sticky bottom-0 bg-white border-t border-gray-200 py-4 px-6 -mx-6 mt-8 shadow-lg">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        <div>
          {error && (
            <p className="text-red-600 text-sm">{error}</p>
          )}
          {success && (
            <p className="text-green-600 text-sm font-medium">
              PPTX downloaded successfully!
            </p>
          )}
        </div>
        <button
          onClick={handleGenerate}
          disabled={loading || !data.header.company_name}
          className="py-3 px-8 bg-cc-dark text-white rounded-lg font-medium text-base
                     hover:bg-cc-mid transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center gap-2 shadow-md"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Generating PPTX...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Generate One-Pager PPTX
            </>
          )}
        </button>
      </div>
    </div>
  );
}

"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { researchCompany } from "@/lib/api";
import { ResearchResponse } from "@/lib/types";
import PromptEditor from "./components/PromptEditor";

export default function InputPage() {
  const router = useRouter();
  const [companyName, setCompanyName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPrompts, setShowPrompts] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleResearch() {
    if (!companyName.trim()) {
      setError("Please enter a company name");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response: ResearchResponse = await researchCompany(
        companyName.trim(),
        file || undefined
      );
      // Store data and verification in sessionStorage, navigate to editor
      sessionStorage.setItem("onePagerData", JSON.stringify(response.data));
      if (response.verification) {
        sessionStorage.setItem("verification", JSON.stringify(response.verification));
      }
      router.push("/editor");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Research failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h2 className="text-2xl font-bold text-cc-dark mb-2">
          New One-Pager
        </h2>
        <p className="text-gray-500 mb-8">
          Enter a company name to start AI research, or upload an Information
          Memorandum (PDF) for faster, more accurate results.
        </p>

        {/* Company Name */}
        <div className="mb-6">
          <label
            htmlFor="company"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Company Name *
          </label>
          <input
            id="company"
            type="text"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleResearch()}
            placeholder="e.g. ACCEL GmbH"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-lg
                       focus:ring-2 focus:ring-cc-mid focus:border-cc-mid transition-all"
            disabled={loading}
          />
        </div>

        {/* PDF Upload */}
        <div className="mb-8">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Information Memorandum (optional)
          </label>
          <div
            className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors
              ${file ? "border-cc-mid bg-blue-50" : "border-gray-300 hover:border-gray-400"}`}
            onClick={() => fileRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const droppedFile = e.dataTransfer.files[0];
              if (droppedFile?.name.endsWith(".pdf")) {
                setFile(droppedFile);
              }
            }}
          >
            <input
              ref={fileRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
            {file ? (
              <div className="flex items-center justify-center gap-3">
                <svg className="w-6 h-6 text-cc-mid" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span className="text-cc-dark font-medium">{file.name}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                  }}
                  className="text-gray-400 hover:text-red-500 ml-2"
                >
                  Remove
                </button>
              </div>
            ) : (
              <div>
                <svg className="w-10 h-10 text-gray-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p className="text-gray-500">
                  Drop PDF here or <span className="text-cc-mid cursor-pointer">browse</span>
                </p>
                <p className="text-xs text-gray-400 mt-1">Max 20 MB</p>
              </div>
            )}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Research Button */}
        <button
          onClick={handleResearch}
          disabled={loading || !companyName.trim()}
          className="w-full py-3 px-6 bg-cc-dark text-white rounded-lg font-medium text-lg
                     hover:bg-cc-mid transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center justify-center gap-3"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Researching with AI...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Research Company
            </>
          )}
        </button>

        {loading && (
          <p className="text-center text-sm text-gray-500 mt-3">
            AI is researching the company using web search and IM analysis.
            This typically takes 30-60 seconds.
          </p>
        )}
      </div>

      {/* Prompt Editor Toggle */}
      <div className="mt-6">
        <button
          onClick={() => setShowPrompts(!showPrompts)}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-cc-mid transition-colors mx-auto"
        >
          <svg
            className={`w-4 h-4 transition-transform ${showPrompts ? "rotate-90" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          {showPrompts ? "Hide AI Prompts" : "Edit AI Prompts"}
        </button>

        {showPrompts && (
          <div className="mt-4 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <PromptEditor />
          </div>
        )}
      </div>

      {/* Skip to editor link */}
      <div className="text-center mt-4">
        <button
          onClick={() => {
            sessionStorage.removeItem("onePagerData");
            router.push("/editor");
          }}
          className="text-sm text-gray-400 hover:text-cc-mid transition-colors"
        >
          Skip research — fill manually
        </button>
      </div>
    </div>
  );
}

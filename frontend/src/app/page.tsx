"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { researchCompany, listJobs, deleteJob } from "@/lib/api";
import { ResearchResponse, JobSummary } from "@/lib/types";
import PromptEditor from "./components/PromptEditor";
import JobCard from "./components/JobCard";

const MAX_FILE_SIZE_MB = 20;

export default function InputPage() {
  const router = useRouter();
  const [companyName, setCompanyName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPrompts, setShowPrompts] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  // Recent jobs
  const [recentJobs, setRecentJobs] = useState<JobSummary[]>([]);
  const [jobsLoading, setJobsLoading] = useState(true);

  useEffect(() => {
    async function fetchRecentJobs() {
      try {
        const jobs = await listJobs();
        jobs.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        setRecentJobs(jobs.slice(0, 5));
      } catch {
        // Silently fail — recent jobs is optional
      } finally {
        setJobsLoading(false);
      }
    }
    fetchRecentJobs();
  }, []);

  function validateFile(f: File): boolean {
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported");
      return false;
    }
    if (f.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setError(`File too large (max ${MAX_FILE_SIZE_MB} MB)`);
      return false;
    }
    setError(null);
    return true;
  }

  function handleFile(f: File | null) {
    if (f && validateFile(f)) {
      setFile(f);
    } else if (!f) {
      setFile(null);
    }
  }

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

      // If the backend returned a job_id, navigate to the job-aware editor
      if (response.job_id) {
        router.push(`/editor/${response.job_id}`);
      } else {
        // Fallback: store in sessionStorage and go to old editor
        sessionStorage.setItem("onePagerData", JSON.stringify(response.data));
        if (response.verification) {
          sessionStorage.setItem("verification", JSON.stringify(response.verification));
        }
        router.push("/editor");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Research failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleDeleteJob(id: string) {
    try {
      await deleteJob(id);
      setRecentJobs((prev) => prev.filter((j) => j.id !== id));
    } catch {
      // Silently fail
    }
  }

  const fileSizeMB = file ? (file.size / (1024 * 1024)).toFixed(1) : null;

  return (
    <div className="max-w-xl mx-auto">
      {/* Main Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200/80 overflow-hidden">
        {/* Card Header */}
        <div className="px-8 pt-8 pb-6 border-b border-gray-100">
          <h2 className="text-xl font-semibold text-cc-dark mb-1">
            New One-Pager
          </h2>
          <p className="text-sm text-gray-500 leading-relaxed">
            Enter a company name and optionally upload an Information Memorandum
            for structured data extraction.
          </p>
        </div>

        <div className="px-8 py-6 space-y-6">
          {/* Company Name */}
          <div>
            <label
              htmlFor="company"
              className="block text-sm font-medium text-gray-700 mb-1.5"
            >
              Company Name
            </label>
            <input
              id="company"
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !loading && handleResearch()}
              placeholder="e.g. ACCEL GmbH"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm
                         focus:ring-2 focus:ring-cc-mid/30 focus:border-cc-mid transition-all
                         placeholder:text-gray-400"
              disabled={loading}
            />
          </div>

          {/* PDF Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Information Memorandum / Teaser
              <span className="text-gray-400 font-normal ml-1">(optional)</span>
            </label>
            <div
              className={`border-2 border-dashed rounded-lg p-5 text-center transition-all cursor-pointer
                ${
                  file
                    ? "border-cc-mid/40 bg-cc-surface"
                    : "border-gray-200 hover:border-cc-mid/30 hover:bg-gray-50"
                }`}
              onClick={() => fileRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                e.currentTarget.classList.add("border-cc-mid/40", "bg-cc-surface");
              }}
              onDragLeave={(e) => {
                e.currentTarget.classList.remove("border-cc-mid/40", "bg-cc-surface");
              }}
              onDrop={(e) => {
                e.preventDefault();
                e.currentTarget.classList.remove("border-cc-mid/40", "bg-cc-surface");
                const droppedFile = e.dataTransfer.files[0];
                if (droppedFile) handleFile(droppedFile);
              }}
            >
              <input
                ref={fileRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => handleFile(e.target.files?.[0] || null)}
              />
              {file ? (
                <div className="flex items-center justify-center gap-3">
                  <div className="w-8 h-8 rounded bg-cc-mid/10 flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-cc-mid" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div className="text-left min-w-0">
                    <p className="text-sm font-medium text-cc-dark truncate">{file.name}</p>
                    <p className="text-xs text-gray-400">{fileSizeMB} MB</p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                    }}
                    className="text-gray-400 hover:text-red-500 ml-auto p-1 rounded hover:bg-red-50 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ) : (
                <div className="py-2">
                  <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-3">
                    <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <p className="text-sm text-gray-500">
                    Drop PDF here or <span className="text-cc-mid font-medium">browse</span>
                  </p>
                  <p className="text-xs text-gray-400 mt-1">PDF up to {MAX_FILE_SIZE_MB} MB</p>
                </div>
              )}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          {/* Research Button */}
          <button
            onClick={handleResearch}
            disabled={loading || !companyName.trim()}
            className="w-full py-2.5 px-6 bg-cc-dark text-white rounded-lg font-medium text-sm
                       hover:bg-cc-mid transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                       flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Researching with AI...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Research Company
              </>
            )}
          </button>

          {loading && (
            <div className="flex items-center gap-3 p-3 bg-cc-surface rounded-lg">
              <div className="w-2 h-2 bg-cc-mid rounded-full animate-pulse" />
              <p className="text-xs text-gray-500">
                AI is researching via web search{file ? " and IM analysis" : ""}. This typically takes 30-60 seconds.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Bottom actions */}
      <div className="flex items-center justify-between mt-5">
        <button
          onClick={() => setShowPrompts(!showPrompts)}
          className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-cc-mid transition-colors"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          {showPrompts ? "Hide Prompts" : "Edit AI Prompts"}
        </button>

        <button
          onClick={() => router.push("/editor")}
          className="text-xs text-gray-400 hover:text-cc-mid transition-colors"
        >
          Skip to manual editor
        </button>
      </div>

      {/* Prompt Editor */}
      {showPrompts && (
        <div className="mt-4 bg-white rounded-xl shadow-sm border border-gray-200/80 p-6">
          <PromptEditor />
        </div>
      )}

      {/* Recent Jobs */}
      {!jobsLoading && recentJobs.length > 0 && (
        <div className="mt-8">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-cc-dark">Recent Jobs</h3>
            <button
              onClick={() => router.push("/jobs")}
              className="text-xs text-gray-400 hover:text-cc-mid transition-colors"
            >
              View all
            </button>
          </div>
          <div className="space-y-2">
            {recentJobs.map((job) => (
              <JobCard key={job.id} job={job} onDelete={handleDeleteJob} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

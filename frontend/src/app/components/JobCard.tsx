"use client";

import { useRouter } from "next/navigation";
import { JobSummary } from "@/lib/types";

interface JobCardProps {
  job: JobSummary;
  onDelete: (id: string) => void;
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHr = Math.floor(diffMin / 60);
  const diffDays = Math.floor(diffHr / 24);

  if (diffSec < 60) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHr < 24) return `${diffHr}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function StatusBadge({ status }: { status: JobSummary["status"] }) {
  const styles: Record<JobSummary["status"], string> = {
    pending: "bg-gray-100 text-gray-600",
    researching: "bg-blue-50 text-blue-600",
    completed: "bg-green-50 text-green-700",
    failed: "bg-red-50 text-red-600",
  };

  const labels: Record<JobSummary["status"], string> = {
    pending: "Pending",
    researching: "Researching",
    completed: "Completed",
    failed: "Failed",
  };

  return (
    <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}

export default function JobCard({ job, onDelete }: JobCardProps) {
  const router = useRouter();

  function handleClick() {
    router.push(`/editor/${job.id}`);
  }

  function handleDelete(e: React.MouseEvent) {
    e.stopPropagation();
    if (window.confirm(`Delete research for "${job.company_name}"? This cannot be undone.`)) {
      onDelete(job.id);
    }
  }

  return (
    <div
      onClick={handleClick}
      className="bg-white rounded-lg border border-gray-200/80 p-4 hover:border-cc-mid/30 hover:shadow-sm
                 transition-all cursor-pointer group"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold text-cc-dark truncate">
              {job.company_name}
            </h3>
            <StatusBadge status={job.status} />
          </div>
          <div className="flex items-center gap-3 text-xs text-gray-400">
            <span>{formatRelativeTime(job.created_at)}</span>
            {job.research_mode === "deep" && (
              <span className="bg-purple-50 text-purple-600 px-1.5 py-0.5 rounded text-[10px] font-medium">
                Deep
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1.5 flex-shrink-0">
          {/* IM document icon */}
          {job.im_filename && (
            <div className="w-6 h-6 rounded bg-gray-50 flex items-center justify-center" title="Has IM document">
              <svg className="w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          )}

          {/* PPTX icon */}
          {job.has_pptx && (
            <div className="w-6 h-6 rounded bg-green-50 flex items-center justify-center" title="PPTX generated">
              <svg className="w-3.5 h-3.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
          )}

          {/* Delete button */}
          <button
            onClick={handleDelete}
            className="w-6 h-6 rounded flex items-center justify-center text-gray-300
                       hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100"
            title="Delete job"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

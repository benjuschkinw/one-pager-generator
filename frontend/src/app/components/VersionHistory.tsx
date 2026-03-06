"use client";

import { useState, useEffect, useCallback } from "react";
import { listVersions, restoreVersion } from "@/lib/api";
import { Version, Job } from "@/lib/types";

interface VersionHistoryProps {
  jobId: string;
  onRestore: (job: Job) => void;
}

export default function VersionHistory({ jobId, onRestore }: VersionHistoryProps) {
  const [versions, setVersions] = useState<Version[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [restoring, setRestoring] = useState<number | null>(null);

  const loadVersions = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await listVersions(jobId);
      setVersions(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load versions");
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    loadVersions();
  }, [loadVersions]);

  async function handleRestore(version: Version) {
    if (
      !confirm(
        `Restore to version ${version.version_number}? The current state will be saved as a new version.`
      )
    ) {
      return;
    }

    setRestoring(version.version_number);
    try {
      const restoredJob = await restoreVersion(jobId, version.version_number);
      onRestore(restoredJob);
      // Reload versions to show the new version
      loadVersions();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to restore version");
    } finally {
      setRestoring(null);
    }
  }

  function formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
        <h3 className="font-medium text-cc-dark">Version History</h3>
      </div>

      <div className="max-h-[600px] overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin h-6 w-6 border-4 border-cc-mid border-t-transparent rounded-full" />
          </div>
        ) : error ? (
          <div className="p-4 text-sm text-red-600">{error}</div>
        ) : versions.length === 0 ? (
          <div className="p-4 text-sm text-gray-500 text-center">
            No version history yet. Versions are created automatically when you edit.
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {versions.map((version) => (
              <div
                key={version.id}
                className="p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                      v{version.version_number}
                    </span>
                    <p className="text-sm text-gray-500 mt-1">
                      {formatDate(version.created_at)}
                    </p>
                    {version.change_summary && (
                      <p className="text-sm text-gray-700 mt-1">
                        {version.change_summary}
                      </p>
                    )}
                  </div>

                  <button
                    onClick={() => handleRestore(version)}
                    disabled={restoring === version.version_number}
                    className="text-xs text-cc-mid hover:text-cc-dark transition-colors disabled:opacity-50"
                  >
                    {restoring === version.version_number ? (
                      "Restoring..."
                    ) : (
                      "Restore"
                    )}
                  </button>
                </div>

                {/* Preview of changes */}
                <div className="mt-2 text-xs text-gray-400">
                  <span>
                    Company: {version.data.header.company_name || "Unnamed"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

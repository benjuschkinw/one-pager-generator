/**
 * API client for the One-Pager Generator backend.
 */

import { OnePagerData, ResearchResponse, PromptDefinition, JobSummary, Job, DeepResearchSSEEvent } from "./types";

const API_BASE = "/api";

/**
 * Research a company using AI.
 * Optionally upload an IM PDF for extraction.
 * Returns data + verification results.
 */
export async function researchCompany(
  companyName: string,
  imFile?: File
): Promise<ResearchResponse> {
  const formData = new FormData();
  formData.append("company_name", companyName);
  if (imFile) {
    formData.append("im_file", imFile);
  }

  const res = await fetch(`${API_BASE}/research`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Research failed");
  }

  return res.json();
}

/**
 * Generate a One-Pager PPTX and trigger download.
 */
export async function generatePptx(data: OnePagerData): Promise<void> {
  const res = await fetch(`${API_BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Generation failed");
  }

  // Trigger download
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;

  // Extract filename from Content-Disposition header
  const disposition = res.headers.get("Content-Disposition");
  const filenameMatch = disposition?.match(/filename="(.+)"/);
  a.download = filenameMatch?.[1] || "One_Pager.pptx";

  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// Job management
// ---------------------------------------------------------------------------

/**
 * List all jobs (summary view).
 */
export async function listJobs(): Promise<JobSummary[]> {
  const res = await fetch(`${API_BASE}/jobs`);
  if (!res.ok) {
    throw new Error("Failed to fetch jobs");
  }
  return res.json();
}

/**
 * Get full job details by ID.
 */
export async function getJob(id: string): Promise<Job> {
  const res = await fetch(`${API_BASE}/jobs/${id}`);
  if (!res.ok) {
    if (res.status === 404) {
      throw new Error("Job not found");
    }
    throw new Error("Failed to fetch job");
  }
  return res.json();
}

/**
 * Delete a job and its associated files.
 */
export async function deleteJob(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/jobs/${id}`, { method: "DELETE" });
  if (!res.ok) {
    throw new Error("Failed to delete job");
  }
}

/**
 * Save edited OnePagerData back to the job.
 */
export async function saveJobData(id: string, data: OnePagerData): Promise<void> {
  const res = await fetch(`${API_BASE}/jobs/${id}/data`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data }),
  });
  if (!res.ok) {
    throw new Error("Failed to save job data");
  }
}

/**
 * Generate a PPTX from a job's data and trigger download.
 */
export async function generateJobPptx(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/jobs/${id}/generate`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Generation failed");
  }

  // Trigger download
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;

  const disposition = res.headers.get("Content-Disposition");
  const filenameMatch = disposition?.match(/filename="(.+)"/);
  a.download = filenameMatch?.[1] || "One_Pager.pptx";

  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Get the URL for downloading the original IM PDF.
 */
export function getJobImUrl(id: string): string {
  return `${API_BASE}/jobs/${id}/im`;
}

/**
 * Get the URL for downloading the generated PPTX.
 */
export function getJobPptxUrl(id: string): string {
  return `${API_BASE}/jobs/${id}/pptx`;
}

// ---------------------------------------------------------------------------
// Deep Research (SSE streaming)
// ---------------------------------------------------------------------------

/**
 * Start deep research for a job. Connects to the SSE endpoint via fetch
 * (since EventSource doesn't support POST). Returns an AbortController
 * so the caller can cancel the stream.
 */
export function startDeepResearch(
  jobId: string,
  onEvent: (event: string, data: DeepResearchSSEEvent) => void,
  onComplete: () => void,
  onError: (error: string) => void,
): AbortController {
  const controller = new AbortController();

  (async () => {
    try {
      const response = await fetch(`${API_BASE}/jobs/${jobId}/research/deep`, {
        method: "POST",
        signal: controller.signal,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: response.statusText }));
        onError(err.detail || "Deep research failed");
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        onError("No response stream available");
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        // Keep the last potentially incomplete line in the buffer
        buffer = lines.pop() || "";

        let currentEvent = "message";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            const dataStr = line.slice(6).trim();
            if (!dataStr) continue;
            try {
              const data: DeepResearchSSEEvent = JSON.parse(dataStr);
              onEvent(currentEvent, data);

              if (currentEvent === "complete" || currentEvent === "error") {
                if (currentEvent === "complete") {
                  onComplete();
                } else {
                  onError(data.message || "Deep research failed");
                }
              }
            } catch {
              // Skip malformed JSON
            }
            currentEvent = "message";
          }
        }
      }

      // Stream ended without explicit complete event — treat as complete
      onComplete();
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      onError(err instanceof Error ? err.message : "Deep research connection failed");
    }
  })();

  return controller;
}

// ---------------------------------------------------------------------------
// Prompt management
// ---------------------------------------------------------------------------

/** Admin key for prompt mutation endpoints. Read from sessionStorage. */
function getAdminHeaders(): Record<string, string> {
  const key = typeof window !== "undefined" ? sessionStorage.getItem("adminApiKey") : null;
  return key ? { "X-Admin-Key": key } : {};
}

/**
 * Fetch all editable prompts.
 */
export async function getPrompts(): Promise<PromptDefinition[]> {
  const res = await fetch(`${API_BASE}/prompts`);
  if (!res.ok) {
    throw new Error("Failed to fetch prompts");
  }
  return res.json();
}

/**
 * Update a prompt's template text. Requires admin key in sessionStorage.
 */
export async function updatePrompt(
  name: string,
  template: string
): Promise<PromptDefinition> {
  const res = await fetch(`${API_BASE}/prompts/${name}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...getAdminHeaders() },
    body: JSON.stringify({ template }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to update prompt");
  }
  return res.json();
}

/**
 * Reset a single prompt to its default. Requires admin key in sessionStorage.
 */
export async function resetPrompt(name: string): Promise<PromptDefinition> {
  const res = await fetch(`${API_BASE}/prompts/${name}/reset`, {
    method: "POST",
    headers: { ...getAdminHeaders() },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to reset prompt");
  }
  return res.json();
}

/**
 * Reset all prompts to defaults. Requires admin key in sessionStorage.
 */
export async function resetAllPrompts(): Promise<PromptDefinition[]> {
  const res = await fetch(`${API_BASE}/prompts/reset`, {
    method: "POST",
    headers: { ...getAdminHeaders() },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to reset prompts");
  }
  return res.json();
}

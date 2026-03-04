/**
 * API client for the One-Pager Generator backend.
 */

import { OnePagerData, ResearchResponse, PromptDefinition } from "./types";

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
// Prompt management
// ---------------------------------------------------------------------------

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
 * Update a prompt's template text.
 */
export async function updatePrompt(
  name: string,
  template: string
): Promise<PromptDefinition> {
  const res = await fetch(`${API_BASE}/prompts/${name}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ template }),
  });
  if (!res.ok) {
    throw new Error("Failed to update prompt");
  }
  return res.json();
}

/**
 * Reset a single prompt to its default.
 */
export async function resetPrompt(name: string): Promise<PromptDefinition> {
  const res = await fetch(`${API_BASE}/prompts/${name}/reset`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error("Failed to reset prompt");
  }
  return res.json();
}

/**
 * Reset all prompts to defaults.
 */
export async function resetAllPrompts(): Promise<PromptDefinition[]> {
  const res = await fetch(`${API_BASE}/prompts/reset`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error("Failed to reset prompts");
  }
  return res.json();
}

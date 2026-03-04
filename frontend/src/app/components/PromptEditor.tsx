"use client";

import { useState, useEffect } from "react";
import { PromptDefinition } from "@/lib/types";
import { getPrompts, updatePrompt, resetPrompt, resetAllPrompts } from "@/lib/api";

/** Friendly display names for prompt keys */
const PROMPT_LABELS: Record<string, string> = {
  research_system: "Research System Prompt (Web Search)",
  research_system_no_search: "Research System Prompt (No Web Search)",
  research_user_with_im: "User Prompt — With IM",
  research_user_no_im: "User Prompt — Without IM",
  verification: "Verification System Prompt",
};

export default function PromptEditor() {
  const [prompts, setPrompts] = useState<PromptDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedPrompt, setExpandedPrompt] = useState<string | null>(null);
  const [saving, setSaving] = useState<string | null>(null);
  const [editedTemplates, setEditedTemplates] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchPrompts();
  }, []);

  async function fetchPrompts() {
    try {
      setLoading(true);
      const data = await getPrompts();
      setPrompts(data);
      setError(null);
    } catch {
      setError("Failed to load prompts");
    } finally {
      setLoading(false);
    }
  }

  function handleEdit(name: string, value: string) {
    setEditedTemplates((prev) => ({ ...prev, [name]: value }));
  }

  function getDisplayTemplate(prompt: PromptDefinition): string {
    return editedTemplates[prompt.name] ?? prompt.template;
  }

  function hasUnsavedChanges(prompt: PromptDefinition): boolean {
    const edited = editedTemplates[prompt.name];
    return edited !== undefined && edited !== prompt.template;
  }

  async function handleSave(name: string) {
    const template = editedTemplates[name];
    if (!template) return;

    setSaving(name);
    try {
      const updated = await updatePrompt(name, template);
      setPrompts((prev) => prev.map((p) => (p.name === name ? updated : p)));
      setEditedTemplates((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    } catch {
      setError(`Failed to save ${name}`);
    } finally {
      setSaving(null);
    }
  }

  async function handleReset(name: string) {
    setSaving(name);
    try {
      const updated = await resetPrompt(name);
      setPrompts((prev) => prev.map((p) => (p.name === name ? updated : p)));
      setEditedTemplates((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    } catch {
      setError(`Failed to reset ${name}`);
    } finally {
      setSaving(null);
    }
  }

  async function handleResetAll() {
    setSaving("all");
    try {
      const updated = await resetAllPrompts();
      setPrompts(updated);
      setEditedTemplates({});
    } catch {
      setError("Failed to reset prompts");
    } finally {
      setSaving(null);
    }
  }

  if (loading) {
    return (
      <div className="text-sm text-gray-400 py-4 text-center">
        Loading prompts...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-sm text-red-500 py-4 text-center">
        {error}
        <button
          onClick={fetchPrompts}
          className="ml-2 text-cc-mid hover:underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">
          AI Prompts
        </h3>
        <button
          onClick={handleResetAll}
          disabled={saving !== null}
          className="text-xs text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
        >
          Reset All to Defaults
        </button>
      </div>

      {prompts.map((prompt) => {
        const isExpanded = expandedPrompt === prompt.name;
        const unsaved = hasUnsavedChanges(prompt);

        return (
          <div
            key={prompt.name}
            className="border border-gray-200 rounded-lg overflow-hidden"
          >
            {/* Header */}
            <button
              onClick={() =>
                setExpandedPrompt(isExpanded ? null : prompt.name)
              }
              className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
            >
              <div className="flex items-center gap-2">
                <svg
                  className={`w-4 h-4 text-gray-400 transition-transform ${
                    isExpanded ? "rotate-90" : ""
                  }`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
                <span className="text-sm font-medium text-gray-700">
                  {PROMPT_LABELS[prompt.name] || prompt.name}
                </span>
                {unsaved && (
                  <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded">
                    unsaved
                  </span>
                )}
                {!prompt.is_default && !unsaved && (
                  <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                    modified
                  </span>
                )}
              </div>
            </button>

            {/* Expanded content */}
            {isExpanded && (
              <div className="p-4 space-y-3">
                <p className="text-xs text-gray-500">{prompt.description}</p>
                <textarea
                  value={getDisplayTemplate(prompt)}
                  onChange={(e) => handleEdit(prompt.name, e.target.value)}
                  className="w-full h-64 px-3 py-2 text-xs font-mono border border-gray-200 rounded-lg
                             focus:ring-2 focus:ring-cc-mid focus:border-cc-mid resize-y"
                  spellCheck={false}
                />
                <div className="flex items-center gap-2 justify-end">
                  {!prompt.is_default && (
                    <button
                      onClick={() => handleReset(prompt.name)}
                      disabled={saving === prompt.name}
                      className="px-3 py-1.5 text-xs text-gray-500 hover:text-red-600 border border-gray-200
                                 rounded-lg hover:border-red-200 transition-colors disabled:opacity-50"
                    >
                      Reset to Default
                    </button>
                  )}
                  {unsaved && (
                    <button
                      onClick={() => handleSave(prompt.name)}
                      disabled={saving === prompt.name}
                      className="px-3 py-1.5 text-xs text-white bg-cc-dark rounded-lg
                                 hover:bg-cc-mid transition-colors disabled:opacity-50"
                    >
                      {saving === prompt.name ? "Saving..." : "Save"}
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

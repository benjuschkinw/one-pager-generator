"use client";

import { useState, useEffect, useCallback } from "react";
import { StepModelInfo, ModelCapabilities } from "@/lib/types";
import { getKnownModels, getStepModels, setStepModel, resetStepModel, resetAllModels } from "@/lib/api";

type Pipeline = "deep" | "market";

function CapBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded ${
        ok ? "bg-green-50 text-green-700" : "bg-gray-100 text-gray-400"
      }`}
    >
      {ok ? (
        <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
        </svg>
      )}
      {label}
    </span>
  );
}

function StepCard({
  step,
  knownModels,
  onModelChange,
}: {
  step: StepModelInfo;
  knownModels: Record<string, ModelCapabilities>;
  onModelChange: (step: string, pipeline: string, model: string | null) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [selectedModel, setSelectedModel] = useState(step.current_model);
  const modelIds = Object.keys(knownModels);

  const caps = knownModels[selectedModel];

  function handleSave() {
    if (selectedModel === step.default_model) {
      onModelChange(step.step, step.pipeline, null); // reset to default
    } else {
      onModelChange(step.step, step.pipeline, selectedModel);
    }
    setEditing(false);
  }

  function handleReset() {
    setSelectedModel(step.default_model);
    onModelChange(step.step, step.pipeline, null);
    setEditing(false);
  }

  // Compute warnings for selected model
  const warnings: string[] = [];
  if (caps) {
    if (step.requires_web_search && !caps.web_search)
      warnings.push("This step requires web search, but selected model does not support it.");
    if (step.requires_tool_calling && !caps.tool_calling)
      warnings.push("This step requires tool calling, but selected model does not support it.");
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-white">
      <div className="flex items-start justify-between mb-2">
        <div>
          <h4 className="text-sm font-semibold text-cc-dark">{step.step.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</h4>
          <p className="text-xs text-gray-500 mt-0.5">{step.description}</p>
        </div>
        {step.is_override && (
          <span className="text-[10px] bg-amber-50 text-amber-700 font-medium px-1.5 py-0.5 rounded">
            Override
          </span>
        )}
      </div>

      {/* Requirements */}
      <div className="flex gap-1.5 mb-2">
        {step.requires_web_search && (
          <span className="text-[10px] bg-blue-50 text-blue-600 font-medium px-1.5 py-0.5 rounded">
            Needs Web Search
          </span>
        )}
        {step.requires_tool_calling && (
          <span className="text-[10px] bg-purple-50 text-purple-600 font-medium px-1.5 py-0.5 rounded">
            Needs Tool Calling
          </span>
        )}
      </div>

      {/* Current model */}
      {!editing ? (
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs font-mono text-cc-mid">{step.current_model}</span>
            {caps && (
              <div className="flex gap-1 mt-1">
                <CapBadge ok={caps.web_search} label="Web" />
                <CapBadge ok={caps.tool_calling} label="Tools" />
                <CapBadge ok={caps.long_context} label="Long Ctx" />
                <CapBadge ok={caps.structured_output} label="Structured" />
              </div>
            )}
          </div>
          <button
            onClick={() => setEditing(true)}
            className="text-xs text-cc-mid hover:text-cc-dark transition-colors"
          >
            Change
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-cc-mid"
          >
            {modelIds.map((id) => (
              <option key={id} value={id}>
                {id} ({knownModels[id].provider}){id === step.default_model ? " — default" : ""}
              </option>
            ))}
          </select>

          {/* Why recommended */}
          <p className="text-[10px] text-gray-400 italic">
            Default: {step.default_model} — {step.why_recommended}
          </p>

          {/* Capability preview */}
          {caps && (
            <div className="flex gap-1">
              <CapBadge ok={caps.web_search} label="Web" />
              <CapBadge ok={caps.tool_calling} label="Tools" />
              <CapBadge ok={caps.long_context} label="Long Ctx" />
              <CapBadge ok={caps.structured_output} label="Structured" />
            </div>
          )}

          {/* Warnings */}
          {warnings.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-2">
              {warnings.map((w, i) => (
                <p key={i} className="text-[10px] text-amber-700 flex items-start gap-1">
                  <svg className="w-3 h-3 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                  {w}
                </p>
              ))}
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={handleSave}
              className="text-xs bg-cc-dark text-white px-3 py-1.5 rounded-lg hover:bg-cc-mid transition-colors"
            >
              Save
            </button>
            <button
              onClick={handleReset}
              className="text-xs text-gray-500 hover:text-cc-dark px-3 py-1.5 rounded-lg border border-gray-200 transition-colors"
            >
              Reset to Default
            </button>
            <button
              onClick={() => {
                setSelectedModel(step.current_model);
                setEditing(false);
              }}
              className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1.5 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function SettingsPage() {
  const [pipeline, setPipeline] = useState<Pipeline>("deep");
  const [steps, setSteps] = useState<StepModelInfo[]>([]);
  const [knownModels, setKnownModels] = useState<Record<string, ModelCapabilities>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resetting, setResetting] = useState(false);
  const [adminKey, setAdminKey] = useState(() =>
    typeof window !== "undefined" ? sessionStorage.getItem("adminApiKey") || "" : ""
  );

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [models, stepData] = await Promise.all([getKnownModels(), getStepModels(pipeline)]);
      setKnownModels(models);
      setSteps(stepData);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load settings");
    } finally {
      setLoading(false);
    }
  }, [pipeline]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleModelChange(step: string, _pipeline: string, model: string | null) {
    try {
      if (model === null) {
        await resetStepModel(pipeline, step);
      } else {
        await setStepModel(pipeline, step, model);
      }
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update model");
    }
  }

  async function handleResetAll() {
    if (!confirm("Reset all model overrides to defaults?")) return;
    try {
      setResetting(true);
      await resetAllModels();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to reset");
    } finally {
      setResetting(false);
    }
  }

  return (
    <div>
      {/* Admin key input */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
        <label className="text-xs font-medium text-gray-600 block mb-1.5">Admin API Key</label>
        <div className="flex gap-2">
          <input
            type="password"
            value={adminKey}
            onChange={(e) => setAdminKey(e.target.value)}
            placeholder="Enter admin key to enable model changes"
            className="flex-1 text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-cc-mid"
          />
          <button
            onClick={() => {
              sessionStorage.setItem("adminApiKey", adminKey);
              setError(null);
            }}
            className="text-xs bg-cc-dark text-white px-4 py-2 rounded-lg hover:bg-cc-mid transition-colors"
          >
            Save Key
          </button>
        </div>
        <p className="text-[10px] text-gray-400 mt-1">Required for changing models. Stored in session only.</p>
      </div>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-cc-dark">Model Configuration</h2>
          <p className="text-xs text-gray-500 mt-1">
            Choose which AI model runs each pipeline step. Warnings show when a model lacks required capabilities.
          </p>
        </div>
        <button
          onClick={handleResetAll}
          disabled={resetting}
          className="text-xs text-red-500 hover:text-red-700 border border-red-200 px-3 py-1.5 rounded-lg
                     hover:border-red-400 transition-all disabled:opacity-50"
        >
          {resetting ? "Resetting..." : "Reset All to Defaults"}
        </button>
      </div>

      {/* Pipeline tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1 w-fit">
        {(["deep", "market"] as Pipeline[]).map((p) => (
          <button
            key={p}
            onClick={() => setPipeline(p)}
            className={`text-xs px-4 py-1.5 rounded-md font-medium transition-colors ${
              pipeline === p
                ? "bg-white text-cc-dark shadow-sm"
                : "text-gray-500 hover:text-cc-dark"
            }`}
          >
            {p === "deep" ? "Deep Research" : "Market Study"}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-xs text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="animate-spin h-6 w-6 border-2 border-cc-mid border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {steps.map((step) => (
            <StepCard
              key={step.step}
              step={step}
              knownModels={knownModels}
              onModelChange={handleModelChange}
            />
          ))}
        </div>
      )}

      {/* Known Models Reference */}
      <div className="mt-8 border-t border-gray-200 pt-6">
        <h3 className="text-sm font-semibold text-cc-dark mb-3">Available Models</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 pr-4 font-medium text-gray-500">Model</th>
                <th className="text-left py-2 pr-4 font-medium text-gray-500">Provider</th>
                <th className="text-center py-2 pr-4 font-medium text-gray-500">Web Search</th>
                <th className="text-center py-2 pr-4 font-medium text-gray-500">Tool Calling</th>
                <th className="text-center py-2 pr-4 font-medium text-gray-500">Long Context</th>
                <th className="text-center py-2 pr-4 font-medium text-gray-500">Structured Output</th>
                <th className="text-left py-2 font-medium text-gray-500">Notes</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(knownModels).map(([id, caps]) => (
                <tr key={id} className="border-b border-gray-100">
                  <td className="py-2 pr-4 font-mono text-cc-mid">{id}</td>
                  <td className="py-2 pr-4 text-gray-600">{caps.provider}</td>
                  <td className="py-2 pr-4 text-center">{caps.web_search ? "✓" : "—"}</td>
                  <td className="py-2 pr-4 text-center">{caps.tool_calling ? "✓" : "—"}</td>
                  <td className="py-2 pr-4 text-center">{caps.long_context ? "✓" : "—"}</td>
                  <td className="py-2 pr-4 text-center">{caps.structured_output ? "✓" : "—"}</td>
                  <td className="py-2 text-gray-500">{caps.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

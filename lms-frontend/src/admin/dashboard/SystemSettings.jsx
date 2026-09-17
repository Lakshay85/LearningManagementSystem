import { useState, useEffect } from "react";
import adminApi from "../../utils/adminApi";
import {
  Settings,
  Save,
  CheckCircle2,
  Cpu,
  Globe,
  Lock,
  Database,
  Layers,
  Sparkles,
  RefreshCw,
  AlertCircle,
} from "lucide-react";

const SystemSettings = () => {
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successKey, setSuccessKey] = useState(null);
  const [error, setError] = useState(null);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await adminApi.getSettings();
      setSettings(res || {});
    } catch (err) {
      setError(err?.message || "Failed to load system settings");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleUpdate = async (key, value) => {
    try {
      setSaving(true);
      await adminApi.updateSetting(key, value);
      setSettings((prev) => ({
        ...prev,
        [key]: { ...prev[key], value },
      }));
      setSuccessKey(key);
      setTimeout(() => setSuccessKey(null), 3000);
    } catch (err) {
      alert(err?.message || `Failed to update ${key}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-xs text-slate-500">Querying platform governance settings...</p>
      </div>
    );
  }

  const platformName = settings.platformName?.value || "Antigravity LMS";
  const allowRegistrations = settings.allowRegistrations?.value ?? true;
  const enableQuizAI = settings.enableQuizAI?.value ?? true;
  const enableStudentRAG = settings.enableStudentRAG?.value ?? true;
  const defaultDailyLimit = settings.defaultDailyLLMLimit?.value ?? 50;
  const defaultMonthlyLimit = settings.defaultMonthlyLLMLimit?.value ?? 500;

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Settings className="w-5 h-5 text-indigo-600" /> Platform Configuration & Governance
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage global feature flags, AI subsystem defaults, and core enterprise branding policies.
          </p>
        </div>

        <button
          onClick={fetchSettings}
          className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition"
          title="Refresh Settings"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" /> {error}
        </div>
      )}

      {/* Section 1: Platform Identity */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <Globe className="w-4 h-4 text-indigo-600" /> Platform Branding & Self-Registration
        </h3>

        <div className="space-y-4 text-xs pt-2">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Platform Brand Name</label>
            <div className="flex items-center gap-3">
              <input
                type="text"
                defaultValue={platformName}
                onBlur={(e) => handleUpdate("platformName", e.target.value)}
                className="max-w-md w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              />
              {successKey === "platformName" && (
                <span className="text-emerald-600 flex items-center gap-1 font-semibold text-xs">
                  <CheckCircle2 className="w-4 h-4" /> Saved
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between py-3 border-t border-slate-100 max-w-2xl">
            <div>
              <div className="font-semibold text-slate-800">Public Self-Registration</div>
              <div className="text-[11px] text-slate-500">
                Allow new students and teachers to create accounts without admin invitation.
              </div>
            </div>
            <button
              onClick={() => handleUpdate("allowRegistrations", !allowRegistrations)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                allowRegistrations ? "bg-indigo-600" : "bg-slate-200"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  allowRegistrations ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Section 2: AI Subsystem & Quota Defaults */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-indigo-600" /> AI Features & Default LLM Quotas
        </h3>
        <p className="text-xs text-slate-500">
          Control global generative AI feature availability and define standard initial quotas for newly created accounts.
        </p>

        <div className="space-y-4 text-xs pt-2">
          {/* Enable Quiz AI Toggle */}
          <div className="flex items-center justify-between py-3 border-t border-slate-100 max-w-2xl">
            <div>
              <div className="font-semibold text-slate-800">AI Quiz Generation</div>
              <div className="text-[11px] text-slate-500">
                Enable faculty to generate high-quality quiz questions automatically from uploaded course documents.
              </div>
            </div>
            <button
              onClick={() => handleUpdate("enableQuizAI", !enableQuizAI)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                enableQuizAI ? "bg-indigo-600" : "bg-slate-200"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  enableQuizAI ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>

          {/* Enable Student RAG Chat Toggle */}
          <div className="flex items-center justify-between py-3 border-t border-slate-100 max-w-2xl">
            <div>
              <div className="font-semibold text-slate-800">Student Course Material RAG Chat</div>
              <div className="text-[11px] text-slate-500">
                Allow students to converse with course notes, slides, and videos using vector embeddings.
              </div>
            </div>
            <button
              onClick={() => handleUpdate("enableStudentRAG", !enableStudentRAG)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                enableStudentRAG ? "bg-indigo-600" : "bg-slate-200"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  enableStudentRAG ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>

          {/* Default Daily & Monthly Quotas for New Users */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-3 border-t border-slate-100 max-w-2xl">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Default Daily LLM Quota
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="0"
                  defaultValue={defaultDailyLimit}
                  onBlur={(e) => handleUpdate("defaultDailyLLMLimit", parseInt(e.target.value, 10))}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-mono text-xs"
                />
                {successKey === "defaultDailyLLMLimit" && (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                )}
              </div>
              <span className="text-[10px] text-slate-400 mt-1 block">Calls/day (0 for unlimited)</span>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Default Monthly LLM Quota
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="0"
                  defaultValue={defaultMonthlyLimit}
                  onBlur={(e) => handleUpdate("defaultMonthlyLLMLimit", parseInt(e.target.value, 10))}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-mono text-xs"
                />
                {successKey === "defaultMonthlyLLMLimit" && (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                )}
              </div>
              <span className="text-[10px] text-slate-400 mt-1 block">Calls/month (0 for unlimited)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Section 3: Read-only System Architecture Status */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <Database className="w-4 h-4 text-indigo-600" /> System Architecture & Runtime
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 text-xs">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
            <span className="text-slate-400 block text-[10px] uppercase font-semibold">API Version</span>
            <span className="font-bold text-slate-800 text-sm mt-0.5 block">2.0.0 (FastAPI Unified)</span>
          </div>
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
            <span className="text-slate-400 block text-[10px] uppercase font-semibold">Vector Engine</span>
            <span className="font-bold text-emerald-700 text-sm mt-0.5 block">pgvector + BGE-Large</span>
          </div>
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
            <span className="text-slate-400 block text-[10px] uppercase font-semibold">Primary LLM Provider</span>
            <span className="font-bold text-indigo-700 text-sm mt-0.5 block">Groq / Qwen 2.5 (Fast)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemSettings;

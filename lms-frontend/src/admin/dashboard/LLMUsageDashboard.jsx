import { useState, useEffect } from "react";
import adminApi from "../../utils/adminApi";
import {
  Cpu,
  Sparkles,
  TrendingUp,
  Activity,
  Layers,
  Award,
  ExternalLink,
  RefreshCw,
  AlertCircle,
} from "lucide-react";

const LLMUsageDashboard = ({ onSelectUser }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchUsage = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await adminApi.getLLMUsageOverview();
      setData(res);
    } catch (err) {
      setError(err?.message || "Failed to load LLM usage telemetry");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsage();
  }, []);

  const formatTokens = (tokens) => {
    if (!tokens) return "0";
    if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(2)}M`;
    if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}k`;
    return tokens.toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-xs text-slate-500">Querying LLM analytics & intelligence telemetry...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 text-center text-rose-600 max-w-md mx-auto">
        <AlertCircle className="w-8 h-8 mx-auto mb-2 text-rose-500" />
        <p className="text-sm font-semibold">{error || "Telemetry unavailable"}</p>
        <button
          onClick={fetchUsage}
          className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold"
        >
          Retry
        </button>
      </div>
    );
  }

  const { summary, byFeature, trend, topUsers } = data;

  // Max calls for bar chart scaling
  const maxTrendCalls = Math.max(...(trend || []).map((t) => t.calls), 1);

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Cpu className="w-5 h-5 text-indigo-600" /> AI & LLM Intelligence Telemetry
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Monitor API token consumption, analyze prompt vs completion costs, and observe top users utilizing generative AI.
          </p>
        </div>

        <button
          onClick={fetchUsage}
          className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition"
          title="Refresh Telemetry"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Calls Today</span>
            <div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{summary?.callsToday || 0}</span>
            <span className="text-xs text-slate-400">requests</span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Calls This Month</span>
            <div className="w-9 h-9 rounded-xl bg-violet-50 text-violet-600 flex items-center justify-center font-bold">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{summary?.callsMonth || 0}</span>
            <span className="text-xs text-slate-400">requests</span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Tokens</span>
            <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{formatTokens(summary?.totalTokens)}</span>
            <span className="text-xs text-slate-400">cumulative</span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Token Distribution</span>
            <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4 space-y-1 text-xs">
            <div className="flex justify-between text-slate-600">
              <span>Prompt:</span>
              <span className="font-mono font-bold text-slate-800">{formatTokens(summary?.promptTokens)}</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Completion:</span>
              <span className="font-mono font-bold text-indigo-600">{formatTokens(summary?.completionTokens)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 30-Day Activity Bar Visualizer */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-indigo-600" /> 30-Day Query Volume Trend
            </h3>
            <p className="text-xs text-slate-400">Total LLM calls recorded per day across all users.</p>
          </div>
        </div>

        <div className="pt-4">
          <div className="h-40 flex items-end gap-1.5 sm:gap-2">
            {(trend || []).map((t, idx) => {
              const heightPercent = Math.max(8, (t.calls / maxTrendCalls) * 100);
              const isToday = idx === trend.length - 1;
              return (
                <div
                  key={t.date}
                  className="flex-1 flex flex-col items-center gap-1 group relative h-full justify-end"
                >
                  {/* Tooltip on hover */}
                  <div className="absolute -top-8 bg-slate-900 text-white text-[10px] font-bold py-1 px-2 rounded-md opacity-0 group-hover:opacity-100 transition pointer-events-none whitespace-nowrap z-10 shadow-lg">
                    {t.date}: {t.calls} calls
                  </div>

                  {/* Bar */}
                  <div
                    style={{
                      height: `${heightPercent}%`,
                      ...(isToday ? { background: "linear-gradient(to top, #4f46e5, #8b5cf6)", backgroundColor: "#4f46e5" } : {})
                    }}
                    className={`w-full rounded-t-md transition-all duration-300 ${
                      isToday
                        ? "shadow-md bg-indigo-600"
                        : t.calls > 0
                        ? "bg-indigo-200 group-hover:bg-indigo-400"
                        : "bg-slate-100"
                    }`}
                  />
                </div>
              );
            })}
          </div>

          <div className="flex justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-100 font-mono">
            <span>{trend?.[0]?.date || "30 days ago"}</span>
            <span>Today ({trend?.[trend?.length - 1]?.date})</span>
          </div>
        </div>
      </div>

      {/* Two Column: By Feature & Top Users Leaderboard */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* By Feature Breakdown */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-600" /> Usage by Feature
          </h3>
          <p className="text-xs text-slate-500">Distribution of queries across application subsystems.</p>

          <div className="space-y-3 pt-2">
            {(byFeature || []).map((f) => (
              <div key={f.feature} className="p-3 bg-slate-50 rounded-xl border border-slate-100 space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-slate-800 capitalize">
                    {f.feature === "rag_chat" ? "Student RAG Chat" : f.feature === "quiz_generation" ? "Quiz AI Generation" : f.feature}
                  </span>
                  <span className="font-mono font-bold text-indigo-600">{f.calls} calls</span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                  <span>Tokens consumed:</span>
                  <span>{formatTokens(f.tokens)}</span>
                </div>
              </div>
            ))}
            {(!byFeature || byFeature.length === 0) && (
              <p className="text-xs text-slate-400 text-center py-6">No calls logged yet.</p>
            )}
          </div>
        </div>

        {/* Top Users Consumption Leaderboard */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Award className="w-4 h-4 text-indigo-600" /> Top Users by AI Consumption
          </h3>
          <p className="text-xs text-slate-500">Accounts with the highest cumulative LLM call count and token expenditure.</p>

          {topUsers && topUsers.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200/80 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    <th className="py-2.5 px-3">User</th>
                    <th className="py-2.5 px-3">Role</th>
                    <th className="py-2.5 px-3 text-right">Calls Count</th>
                    <th className="py-2.5 px-3 text-right">Tokens Consumed</th>
                    <th className="py-2.5 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {topUsers.map((u, idx) => (
                    <tr key={u.id} className="hover:bg-slate-50/50">
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-slate-100 text-slate-700 font-bold text-[10px] flex items-center justify-center font-mono">
                            {idx + 1}
                          </span>
                          <div>
                            <div className="font-bold text-slate-800">{u.name}</div>
                            <div className="text-[11px] text-slate-400">{u.email}</div>
                          </div>
                        </div>
                      </td>

                      <td className="py-3 px-3">
                        <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-[10px] font-semibold uppercase">
                          {u.role}
                        </span>
                      </td>

                      <td className="py-3 px-3 text-right font-mono font-bold text-slate-800">
                        {u.calls}
                      </td>

                      <td className="py-3 px-3 text-right font-mono font-bold text-indigo-600">
                        {formatTokens(u.tokens)}
                      </td>

                      <td className="py-3 px-3 text-right">
                        <button
                          onClick={() => onSelectUser(u.id)}
                          className="px-2 py-1 text-indigo-600 hover:bg-indigo-50 rounded-md font-semibold text-xs transition"
                        >
                          Configure Limit &rarr;
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-xs text-slate-400 text-center py-10">
              No user consumption records logged yet.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default LLMUsageDashboard;

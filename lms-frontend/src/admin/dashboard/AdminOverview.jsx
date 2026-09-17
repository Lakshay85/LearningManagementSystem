import { useState, useEffect } from "react";
import adminApi from "../../utils/adminApi";
import {
  Users,
  BookOpen,
  FolderOpen,
  ClipboardCheck,
  Cpu,
  ShieldCheck,
  HardDrive,
  TrendingUp,
  UserPlus,
  Sliders,
  History,
  AlertCircle,
  RefreshCw,
  ArrowUpRight,
  Activity,
} from "lucide-react";

const AdminOverview = ({ setActiveTab, onSelectUser }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminApi.getDashboardStats();
      setStats(data);
    } catch (err) {
      setError(err?.message || "Failed to load dashboard statistics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const formatStorage = (bytes) => {
    if (!bytes || bytes === 0) return "0 MB";
    const mb = bytes / (1024 * 1024);
    if (mb < 1024) return `${mb.toFixed(1)} MB`;
    return `${(mb / 1024).toFixed(2)} GB`;
  };

  const formatTokens = (tokens) => {
    if (!tokens) return "0";
    if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(1)}M`;
    if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}k`;
    return tokens.toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="w-10 h-10 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-slate-500 font-medium text-sm">Loading platform telemetry...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-center max-w-lg mx-auto my-12">
        <AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
        <h3 className="text-base font-bold text-rose-800">Telemetry Unavailable</h3>
        <p className="text-xs text-rose-600 mt-1">{error}</p>
        <button
          onClick={fetchStats}
          className="mt-4 px-4 py-2 bg-rose-600 text-white rounded-xl text-xs font-semibold hover:bg-rose-700 transition"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const { users, courses, content, llm, recentActivities } = stats || {};

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Welcome Banner */}
      <div
        className="relative overflow-hidden text-white rounded-2xl p-8 shadow-xl border border-indigo-950/20"
        style={{
          background: "linear-gradient(135deg, #1e1b4b 0%, #312e81 45%, #0f172a 100%)",
          backgroundColor: "#1e1b4b",
        }}
      >
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md text-xs font-semibold text-indigo-200 border border-white/20">
              <ShieldCheck className="w-3.5 h-3.5 text-indigo-300" />
              Role-Based Access Control Active
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Enterprise Command Center
            </h2>
            <p className="text-indigo-200 text-sm max-w-xl leading-relaxed">
              Monitor real-time system performance, govern faculty content, inspect LLM consumption quotas, and enforce platform security policies.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setActiveTab("users")}
              className="px-4 py-2.5 bg-white text-indigo-950 font-bold text-xs rounded-xl shadow-lg hover:bg-indigo-50 transition flex items-center gap-2 cursor-pointer"
            >
              <UserPlus className="w-4 h-4 text-indigo-600" /> Manage Users
            </button>
            <button
              onClick={fetchStats}
              className="p-2.5 bg-white/15 text-white hover:bg-white/25 rounded-xl transition backdrop-blur-md cursor-pointer border border-white/10"
              title="Refresh Telemetry"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Subtle background decoration */}
        <div className="absolute -right-16 -bottom-16 w-64 h-64 bg-indigo-500/30 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute right-40 -top-20 w-48 h-48 bg-violet-500/25 rounded-full blur-2xl pointer-events-none" />
      </div>

      {/* Primary Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Users Card */}
        <div
          onClick={() => setActiveTab("users")}
          className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs hover:shadow-md hover:border-indigo-200 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Users</span>
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:bg-indigo-600 group-hover:text-white transition-colors">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{users?.total || 0}</span>
            <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
              {users?.active || 0} active
            </span>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-3 text-center text-xs">
            <div>
              <span className="block font-bold text-slate-700">{users?.students || 0}</span>
              <span className="text-slate-400 text-[10px]">Students</span>
            </div>
            <div>
              <span className="block font-bold text-slate-700">{users?.faculty || 0}</span>
              <span className="text-slate-400 text-[10px]">Faculty</span>
            </div>
            <div>
              <span className="block font-bold text-slate-700">{users?.admins || 0}</span>
              <span className="text-slate-400 text-[10px]">Admins</span>
            </div>
          </div>
        </div>

        {/* Courses Card */}
        <div
          onClick={() => setActiveTab("courses")}
          className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs hover:shadow-md hover:border-emerald-200 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Courses</span>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center group-hover:bg-emerald-600 group-hover:text-white transition-colors">
              <BookOpen className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{courses?.total || 0}</span>
            <span className="text-xs font-semibold text-slate-500">
              {courses?.enrollments || 0} enrollments
            </span>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded-md">
              {courses?.published || 0} Published
            </span>
            <span className="text-amber-700 font-medium bg-amber-50 px-2 py-0.5 rounded-md">
              {courses?.drafts || 0} Drafts
            </span>
          </div>
        </div>

        {/* LLM Usage Card */}
        <div
          onClick={() => setActiveTab("llm-usage")}
          className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs hover:shadow-md hover:border-violet-200 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">LLM Intelligence</span>
            <div className="w-10 h-10 rounded-xl bg-violet-50 text-violet-600 flex items-center justify-center group-hover:bg-violet-600 group-hover:text-white transition-colors">
              <Cpu className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{llm?.callsToday || 0}</span>
            <span className="text-xs font-medium text-slate-400">calls today</span>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-600">
              <span className="font-bold text-slate-800">{llm?.callsMonth || 0}</span> this month
            </span>
            <span className="text-violet-700 font-semibold bg-violet-50 px-2 py-0.5 rounded-md">
              {formatTokens(llm?.totalTokens)} tokens
            </span>
          </div>
        </div>

        {/* Content & Storage Card */}
        <div
          onClick={() => setActiveTab("content")}
          className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs hover:shadow-md hover:border-blue-200 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Content & Files</span>
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center group-hover:bg-blue-600 group-hover:text-white transition-colors">
              <HardDrive className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">
              {formatStorage(content?.storageBytes)}
            </span>
            <span className="text-xs font-medium text-slate-400">total storage</span>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
            <span>
              <span className="font-bold text-slate-800">{content?.documents || 0}</span> docs
            </span>
            <span>
              <span className="font-bold text-slate-800">{content?.videos || 0}</span> videos
            </span>
            <span>
              <span className="font-bold text-slate-800">{content?.quizzes || 0}</span> quizzes
            </span>
          </div>
        </div>
      </div>

      {/* Two Column Layout: Quick Actions & Recent Activities */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Quick Actions & System Governance */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
          <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-indigo-600" /> Platform Governance
          </h3>
          <p className="text-xs text-slate-500">
            Direct shortcuts to key administrative and compliance controls.
          </p>

          <div className="space-y-2 pt-2">
            <button
              onClick={() => setActiveTab("users")}
              className="w-full flex items-center justify-between p-3 rounded-xl border border-slate-100 hover:border-indigo-200 hover:bg-indigo-50/50 transition text-left group"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
                  <Users className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-800">User Access & Roles</div>
                  <div className="text-[11px] text-slate-400">Assign roles, activate or revoke access</div>
                </div>
              </div>
              <ArrowUpRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition" />
            </button>

            <button
              onClick={() => setActiveTab("llm-usage")}
              className="w-full flex items-center justify-between p-3 rounded-xl border border-slate-100 hover:border-violet-200 hover:bg-violet-50/50 transition text-left group"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center font-bold">
                  <Cpu className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-800">LLM Quota Management</div>
                  <div className="text-[11px] text-slate-400">Configure per-user daily limits & inspect calls</div>
                </div>
              </div>
              <ArrowUpRight className="w-4 h-4 text-slate-400 group-hover:text-violet-600 group-hover:translate-x-0.5 transition" />
            </button>

            <button
              onClick={() => setActiveTab("courses")}
              className="w-full flex items-center justify-between p-3 rounded-xl border border-slate-100 hover:border-emerald-200 hover:bg-emerald-50/50 transition text-left group"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
                  <BookOpen className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-800">Course & Content Moderation</div>
                  <div className="text-[11px] text-slate-400">Review faculty courses, unpublish or remove content</div>
                </div>
              </div>
              <ArrowUpRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-600 group-hover:translate-x-0.5 transition" />
            </button>

            <button
              onClick={() => setActiveTab("audit-logs")}
              className="w-full flex items-center justify-between p-3 rounded-xl border border-slate-100 hover:border-amber-200 hover:bg-amber-50/50 transition text-left group"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
                  <History className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-800">Security Audit Logs</div>
                  <div className="text-[11px] text-slate-400">Immutable trace of all administrative operations</div>
                </div>
              </div>
              <ArrowUpRight className="w-4 h-4 text-slate-400 group-hover:text-amber-600 group-hover:translate-x-0.5 transition" />
            </button>
          </div>
        </div>

        {/* Right: Recent Audit Activities */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-600" /> Recent Administrative Activity
            </h3>
            <button
              onClick={() => setActiveTab("audit-logs")}
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition"
            >
              View Full Audit Log &rarr;
            </button>
          </div>

          {recentActivities && recentActivities.length > 0 ? (
            <div className="divide-y divide-slate-100">
              {recentActivities.map((act) => (
                <div key={act.id} className="py-3 flex items-start justify-between gap-4">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-700">
                        {act.action}
                      </span>
                      <span className="text-xs font-semibold text-slate-800">
                        by {act.actorName}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500">
                      Target: <span className="font-mono text-[11px] text-slate-600">{act.targetType || "system"}</span> {act.targetId ? `(${act.targetId})` : ""}
                    </div>
                  </div>
                  <div className="text-[11px] text-slate-400 whitespace-nowrap">
                    {act.createdAt ? new Date(act.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "Just now"}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-12 text-center text-slate-400 text-xs">
              No recent administrative actions recorded yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminOverview;

import { useState, useEffect } from "react";
import adminApi from "../../utils/adminApi";
import {
  ArrowLeft,
  User,
  Mail,
  Phone,
  Calendar,
  Shield,
  Cpu,
  Save,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Activity,
  Award,
  BookOpen,
  FolderOpen,
  Layers,
  Sparkles,
} from "lucide-react";

const ALL_PERMISSIONS = [
  { id: "users.view", label: "View Users", category: "User Management" },
  { id: "users.manage", label: "Manage Users (Create/Edit/Status)", category: "User Management" },
  { id: "users.delete", label: "Delete Users", category: "User Management" },

  { id: "courses.view_all", label: "View All Courses", category: "Course Oversight" },
  { id: "courses.manage", label: "Manage Courses (Unpublish)", category: "Course Oversight" },

  { id: "content.view_all", label: "View All Content & Media", category: "Content Oversight" },
  { id: "content.manage", label: "Remove Content & Media", category: "Content Oversight" },

  { id: "quizzes.view_all", label: "View All Quizzes", category: "Quiz Oversight" },
  { id: "quizzes.manage", label: "Archive Quizzes", category: "Quiz Oversight" },

  { id: "llm.view_usage", label: "View LLM Intelligence Telemetry", category: "AI & LLM Governance" },
  { id: "llm.configure", label: "Configure LLM Limits & Quotas", category: "AI & LLM Governance" },

  { id: "system.settings", label: "Manage Platform System Settings", category: "System & Audit" },
  { id: "audit.logs_view", label: "Inspect Security Audit Logs", category: "System & Audit" },
  { id: "admin.manage", label: "Manage Administrator Roles", category: "System & Audit" },
];

const UserDetail = ({ userId, onBack }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Quota form
  const [dailyLimit, setDailyLimit] = useState("");
  const [monthlyLimit, setMonthlyLimit] = useState("");
  const [savingQuotas, setSavingQuotas] = useState(false);
  const [quotaSuccess, setQuotaSuccess] = useState(false);

  // Permissions form
  const [selectedPermissions, setSelectedPermissions] = useState([]);
  const [savingPermissions, setSavingPermissions] = useState(false);
  const [permSuccess, setPermSuccess] = useState(false);

  const fetchDetail = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await adminApi.getUser(userId);
      setData(res);
      setDailyLimit(res.llmDailyLimit === null ? "" : String(res.llmDailyLimit));
      setMonthlyLimit(res.llmMonthlyLimit === null ? "" : String(res.llmMonthlyLimit));
      setSelectedPermissions(res.roleDetails?.permissions || []);
    } catch (err) {
      setError(err?.message || "Failed to load user details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userId) fetchDetail();
  }, [userId]);

  const handleSaveQuotas = async (e) => {
    e.preventDefault();
    try {
      setSavingQuotas(true);
      const d = dailyLimit === "" ? null : parseInt(dailyLimit, 10);
      const m = monthlyLimit === "" ? null : parseInt(monthlyLimit, 10);
      await adminApi.setUserLLMLimits(userId, {
        llmDailyLimit: d,
        llmMonthlyLimit: m,
      });
      setQuotaSuccess(true);
      setTimeout(() => setQuotaSuccess(false), 3000);
      fetchDetail();
    } catch (err) {
      alert(err?.message || "Failed to save LLM quotas");
    } finally {
      setSavingQuotas(false);
    }
  };

  const handlePermissionToggle = (permId) => {
    setSelectedPermissions((prev) =>
      prev.includes(permId) ? prev.filter((p) => p !== permId) : [...prev, permId]
    );
  };

  const handleSavePermissions = async () => {
    try {
      setSavingPermissions(true);
      await adminApi.updateAdminPermissions(userId, selectedPermissions);
      setPermSuccess(true);
      setTimeout(() => setPermSuccess(false), 3000);
      fetchDetail();
    } catch (err) {
      alert(err?.message || "Failed to update admin permissions");
    } finally {
      setSavingPermissions(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-xs text-slate-500">Retrieving user telemetry and profiles...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 text-center text-rose-600 max-w-md mx-auto">
        <AlertCircle className="w-8 h-8 mx-auto mb-2 text-rose-500" />
        <p className="text-sm font-semibold">{error || "User not found"}</p>
        <button
          onClick={onBack}
          className="mt-4 px-4 py-2 bg-slate-800 text-white rounded-xl text-xs font-semibold"
        >
          Back to Users
        </button>
      </div>
    );
  }

  const { roleDetails, llmStats, recentLLMLogs } = data;

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Bar with Back Button */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl border border-slate-200 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
        >
          <ArrowLeft className="w-4 h-4" /> Back to User Directory
        </button>

        <div className="flex items-center gap-2">
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
              data.role === "admin"
                ? "bg-violet-100 text-violet-700"
                : data.role === "faculty"
                ? "bg-emerald-100 text-emerald-700"
                : "bg-blue-100 text-blue-700"
            }`}
          >
            {data.role}
          </span>
          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold ${
              data.isActive
                ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                : "bg-rose-50 text-rose-700 border border-rose-200"
            }`}
          >
            {data.isActive ? "Active" : "Inactive"}
          </span>
        </div>
      </div>

      {/* User Identity Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div
            className="w-16 h-16 rounded-2xl text-white flex items-center justify-center font-bold text-xl shadow-md"
            style={{
              background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
              backgroundColor: "#4f46e5",
            }}
          >
            {`${(data.firstName?.[0] || "U")}${(data.lastName?.[0] || "")}`.toUpperCase()}
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              {data.firstName} {data.lastName}
            </h2>
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 mt-1">
              <span className="flex items-center gap-1">
                <Mail className="w-3.5 h-3.5 text-slate-400" /> {data.email}
              </span>
              {data.phoneNumber && (
                <span className="flex items-center gap-1">
                  <Phone className="w-3.5 h-3.5 text-slate-400" /> {data.phoneNumber}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" /> Joined{" "}
                {data.createdAt ? new Date(data.createdAt).toLocaleDateString() : "—"}
              </span>
            </div>
          </div>
        </div>

        {/* Role Specific Stats Pill */}
        <div className="flex items-center gap-4 bg-slate-50 p-3.5 rounded-xl border border-slate-100 text-xs">
          {data.role === "student" && (
            <>
              <div>
                <span className="block font-bold text-slate-800 text-sm">
                  {roleDetails?.enrollmentCount || 0}
                </span>
                <span className="text-slate-400 text-[11px]">Enrolled Courses</span>
              </div>
              <div className="h-6 w-px bg-slate-200" />
              <div>
                <span className="block font-bold text-slate-800 text-sm">
                  {roleDetails?.quizSubmissionsCount || 0}
                </span>
                <span className="text-slate-400 text-[11px]">Quizzes Taken</span>
              </div>
            </>
          )}

          {data.role === "faculty" && (
            <>
              <div>
                <span className="block font-bold text-slate-800 text-sm">
                  {roleDetails?.courseCount || 0}
                </span>
                <span className="text-slate-400 text-[11px]">Courses Created</span>
              </div>
              <div className="h-6 w-px bg-slate-200" />
              <div>
                <span className="block font-bold text-slate-800 text-sm">
                  {(roleDetails?.documentsCount || 0) + (roleDetails?.videosCount || 0)}
                </span>
                <span className="text-slate-400 text-[11px]">Files Uploaded</span>
              </div>
            </>
          )}

          {data.role === "admin" && (
            <div>
              <span className="block font-bold text-violet-700 text-sm uppercase">
                {roleDetails?.adminLevel || "Standard"}
              </span>
              <span className="text-slate-400 text-[11px]">Admin Clearance</span>
            </div>
          )}
        </div>
      </div>

      {/* Grid: LLM Quota Settings & Intelligence Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LLM Quota Controls */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-indigo-600" /> LLM Usage Quotas & Limits
            </h3>
            {quotaSuccess && (
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full animate-fade-in">
                <CheckCircle2 className="w-3.5 h-3.5" /> Quotas Saved
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500">
            Set maximum daily and monthly AI query quotas for this user (RAG document chats and AI quiz generation). Set blank or 0 for unlimited.
          </p>

          <form onSubmit={handleSaveQuotas} className="space-y-4 text-xs pt-2">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Daily Call Quota
                </label>
                <input
                  type="number"
                  min="0"
                  placeholder="e.g. 50 (blank = ∞)"
                  value={dailyLimit}
                  onChange={(e) => setDailyLimit(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-xs font-mono"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Monthly Call Quota
                </label>
                <input
                  type="number"
                  min="0"
                  placeholder="e.g. 500 (blank = ∞)"
                  value={monthlyLimit}
                  onChange={(e) => setMonthlyLimit(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-xs font-mono"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-[11px] text-slate-400">
                Current limit: {data.llmDailyLimit ? `${data.llmDailyLimit}/day` : "Unlimited/day"}
              </span>
              <button
                type="submit"
                disabled={savingQuotas}
                className="px-4 py-2 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition flex items-center gap-2 shadow-xs disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                {savingQuotas ? "Saving..." : "Save Quotas"}
              </button>
            </div>
          </form>
        </div>

        {/* User LLM Activity Stats */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-600" /> AI Consumption Telemetry
          </h3>
          <p className="text-xs text-slate-500">
            Overview of AI requests performed by this user across RAG chat sessions and quiz generation.
          </p>

          <div className="grid grid-cols-3 gap-3 pt-2 text-center">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <span className="text-xl font-extrabold text-slate-900 block">
                {llmStats?.callsToday || 0}
              </span>
              <span className="text-[11px] text-slate-400 font-medium">Calls Today</span>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <span className="text-xl font-extrabold text-slate-900 block">
                {llmStats?.callsMonth || 0}
              </span>
              <span className="text-[11px] text-slate-400 font-medium">Calls This Month</span>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <span className="text-xl font-extrabold text-indigo-600 block">
                {(llmStats?.totalTokens || 0).toLocaleString()}
              </span>
              <span className="text-[11px] text-slate-400 font-medium">Tokens Consumed</span>
            </div>
          </div>
        </div>
      </div>

      {/* Admin Permissions Configuration (Only for admin role) */}
      {data.role === "admin" && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Shield className="w-5 h-5 text-violet-600" /> Granular RBAC Permissions
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Check or uncheck individual permission capabilities granted to this administrator. Super admins bypass all restrictions.
              </p>
            </div>

            <div className="flex items-center gap-3">
              {permSuccess && (
                <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full animate-fade-in">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Permissions Updated
                </span>
              )}
              <button
                onClick={handleSavePermissions}
                disabled={savingPermissions}
                className="px-4 py-2 bg-violet-600 text-white font-semibold text-xs rounded-xl hover:bg-violet-700 transition flex items-center gap-2 shadow-xs disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                {savingPermissions ? "Saving..." : "Save Permissions"}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
            {ALL_PERMISSIONS.map((perm) => {
              const isChecked = selectedPermissions.includes(perm.id);
              return (
                <label
                  key={perm.id}
                  className={`p-3 rounded-xl border flex items-start gap-3 cursor-pointer transition ${
                    isChecked
                      ? "bg-violet-50/60 border-violet-200 text-violet-900"
                      : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => handlePermissionToggle(perm.id)}
                    className="mt-0.5 w-4 h-4 rounded text-violet-600 focus:ring-violet-500 border-slate-300"
                  />
                  <div className="text-xs">
                    <div className="font-semibold">{perm.label}</div>
                    <div className="font-mono text-[10px] text-slate-400 mt-0.5">{perm.id}</div>
                  </div>
                </label>
              );
            })}
          </div>
        </div>
      )}

      {/* Recent LLM Calls Log Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-600" /> Recent AI Query Logs
        </h3>

        {recentLLMLogs && recentLLMLogs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200/80 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3">Feature</th>
                  <th className="py-2.5 px-3">Model</th>
                  <th className="py-2.5 px-3 text-right">Prompt Tokens</th>
                  <th className="py-2.5 px-3 text-right">Completion Tokens</th>
                  <th className="py-2.5 px-3 text-right">Total Tokens</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                {recentLLMLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-3 text-slate-500 font-sans">
                      {log.createdAt ? new Date(log.createdAt).toLocaleString() : "—"}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-semibold text-[10px]">
                        {log.feature}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">{log.model}</td>
                    <td className="py-2.5 px-3 text-right text-slate-500">{log.promptTokens}</td>
                    <td className="py-2.5 px-3 text-right text-slate-500">{log.completionTokens}</td>
                    <td className="py-2.5 px-3 text-right font-bold text-indigo-600">{log.totalTokens}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-xs text-slate-400 py-6 text-center">
            No LLM calls recorded for this user yet.
          </p>
        )}
      </div>
    </div>
  );
};

export default UserDetail;

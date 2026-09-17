import { useState, useEffect } from "react";
import adminApi from "../../utils/adminApi";
import CustomSelect from "../../components/common/CustomSelect";
import {
  History,
  Search,
  Filter,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Shield,
  Eye,
  Terminal,
} from "lucide-react";

const AuditLogViewer = () => {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [actionFilter, setActionFilter] = useState("");
  const [targetTypeFilter, setTargetTypeFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedDetails, setSelectedDetails] = useState(null);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const res = await adminApi.getAuditLogs({
        action: actionFilter,
        targetType: targetTypeFilter,
        page,
        limit,
      });
      setLogs(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error("Failed to load audit logs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page, actionFilter, targetTypeFilter]);

  const totalPages = Math.ceil(total / limit) || 1;

  const getActionBadgeClass = (action) => {
    if (action.includes("created") || action.includes("activated")) {
      return "bg-emerald-50 text-emerald-700 border-emerald-200/60";
    }
    if (action.includes("deleted") || action.includes("removed")) {
      return "bg-rose-50 text-rose-700 border-rose-200/60";
    }
    if (action.includes("deactivated") || action.includes("unpublished")) {
      return "bg-amber-50 text-amber-700 border-amber-200/60";
    }
    return "bg-indigo-50 text-indigo-700 border-indigo-200/60";
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <History className="w-5 h-5 text-indigo-600" /> Administrative Security Audit Trail
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Immutable forensic log of all administrative actions, permission mutations, quota adjustments, and content moderation events.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Action Filter */}
          <div className="w-44">
            <CustomSelect
              value={actionFilter}
              onChange={(e) => {
                setActionFilter(e.target.value);
                setPage(1);
              }}
              size="sm"
              className="bg-slate-50 border-slate-200"
            >
              <option value="">All Action Types</option>
              <option value="user.created">User Created</option>
              <option value="user.updated">User Updated</option>
              <option value="user.activated">User Activated</option>
              <option value="user.deactivated">User Deactivated</option>
              <option value="user.deleted">User Deleted</option>
              <option value="user.role_changed">User Role Changed</option>
              <option value="llm.limit_changed">LLM Quota Changed</option>
              <option value="course.unpublished">Course Unpublished</option>
              <option value="content.removed">Content Removed</option>
              <option value="quiz.removed">Quiz Archived</option>
              <option value="system.setting_changed">Setting Changed</option>
            </CustomSelect>
          </div>

          {/* Target Type Filter */}
          <div className="w-36">
            <CustomSelect
              value={targetTypeFilter}
              onChange={(e) => {
                setTargetTypeFilter(e.target.value);
                setPage(1);
              }}
              size="sm"
              className="bg-slate-50 border-slate-200"
            >
              <option value="">All Targets</option>
              <option value="user">User</option>
              <option value="course">Course</option>
              <option value="document">Document</option>
              <option value="video">Video</option>
              <option value="quiz">Quiz</option>
              <option value="system">System</option>
            </CustomSelect>
          </div>
        </div>

        <button
          onClick={fetchLogs}
          className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition"
          title="Refresh Logs"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        {loading ? (
          <div className="py-20 text-center">
            <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-xs text-slate-500">Querying security audit trails...</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="py-16 text-center text-slate-400 text-xs">
            No audit log records match your filter criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200/80 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Timestamp</th>
                  <th className="py-3.5 px-4">Actor</th>
                  <th className="py-3.5 px-4">Action</th>
                  <th className="py-3.5 px-4">Target</th>
                  <th className="py-3.5 px-4">Origin IP</th>
                  <th className="py-3.5 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/70 transition">
                    <td className="py-3.5 px-4 font-mono text-[11px] text-slate-500">
                      {log.createdAt ? new Date(log.createdAt).toLocaleString() : "—"}
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="font-bold text-slate-800">{log.actorName}</div>
                      <div className="text-[11px] text-slate-400">{log.actorEmail}</div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-md border text-[10px] font-bold uppercase tracking-wider ${getActionBadgeClass(
                          log.action
                        )}`}
                      >
                        {log.action}
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-700 capitalize">
                        {log.targetType || "system"}
                      </div>
                      {log.targetId && (
                        <div className="font-mono text-[10px] text-slate-400">
                          ID: {log.targetId.slice(0, 10)}...
                        </div>
                      )}
                    </td>

                    <td className="py-3.5 px-4 font-mono text-[11px] text-slate-500">
                      {log.ipAddress || "127.0.0.1"}
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      {log.details ? (
                        <button
                          onClick={() => setSelectedDetails({ action: log.action, details: log.details })}
                          className="px-2.5 py-1 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-100 text-[11px] font-medium transition"
                        >
                          View Diff
                        </button>
                      ) : (
                        <span className="text-slate-300 text-[11px]">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        <div className="p-4 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between text-xs text-slate-500">
          <div>
            Showing <span className="font-bold text-slate-700">{logs.length}</span> of{" "}
            <span className="font-bold text-slate-700">{total}</span> records
          </div>

          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span>
              Page {page} of {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40 transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Modal: View Details / Diff */}
      {selectedDetails && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Terminal className="w-4 h-4 text-indigo-600" /> Action Payload: {selectedDetails.action}
              </h3>
              <button
                onClick={() => setSelectedDetails(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            <pre className="p-4 bg-slate-900 text-emerald-400 rounded-xl text-xs font-mono overflow-x-auto max-h-80">
              {JSON.stringify(selectedDetails.details, null, 2)}
            </pre>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedDetails(null)}
                className="px-4 py-2 bg-slate-100 text-slate-700 font-semibold rounded-xl text-xs hover:bg-slate-200 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditLogViewer;

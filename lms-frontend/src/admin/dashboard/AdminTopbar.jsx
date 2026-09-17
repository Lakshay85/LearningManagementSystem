import { ShieldCheck, Activity, Bell, Search, Sparkles } from "lucide-react";

const TAB_TITLES = {
  dashboard: "Platform Overview",
  users: "User & Role Management",
  "user-detail": "User Profile & Quotas",
  courses: "Course Oversight",
  content: "Content & Media Management",
  quizzes: "Assessment & Quiz Oversight",
  "llm-usage": "LLM Usage & Intelligence Controls",
  "audit-logs": "System Audit Trail",
  settings: "Platform Settings & Governance",
};

const AdminTopbar = ({ user, activeTab, onToggleNotifications }) => {
  const title = TAB_TITLES[activeTab] || "Admin Console";
  const fullName = `${user?.firstName || "Super"} ${user?.lastName || "Admin"}`.trim();
  const initials = `${(user?.firstName?.[0] || "A")}${(user?.lastName?.[0] || "D")}`.toUpperCase();

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between z-20 shadow-xs">
      {/* Left: Current Section Title & Breadcrumb */}
      <div className="flex items-center gap-3">
        <div>
          <h1 className="text-lg font-bold text-slate-800 tracking-tight flex items-center gap-2">
            {title}
          </h1>
          <p className="text-xs text-slate-400 font-medium hidden sm:block">
            LMS Platform Administration & Control Center
          </p>
        </div>
      </div>

      {/* Right: Actions & User info */}
      <div className="flex items-center gap-4 flex-shrink-0">
        {/* System status pill */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200/60 text-emerald-700 text-xs font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>System Healthy</span>
        </div>

        {/* Notification bell */}
        <button
          onClick={onToggleNotifications}
          className="relative p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          title="Notifications"
        >
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-indigo-600" />
        </button>

        <div className="h-6 w-px bg-slate-200" />

        {/* Admin Profile */}
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl text-white flex items-center justify-center font-bold text-xs shadow-sm"
            style={{
              background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
              backgroundColor: "#4f46e5",
            }}
          >
            {initials}
          </div>
          <div className="flex flex-col text-left">
            <span className="text-sm font-semibold text-slate-800 leading-tight">
              {fullName}
            </span>
            <span className="text-[11px] font-medium text-indigo-600 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" /> Administrator
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default AdminTopbar;

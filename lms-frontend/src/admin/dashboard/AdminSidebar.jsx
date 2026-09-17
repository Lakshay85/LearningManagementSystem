import { useState } from "react";
import LogoutModal from "../../components/common/LogoutModal";
import LmsLogo from "../../components/common/LmsLogo";
import {
  LayoutDashboard,
  Users,
  BookOpen,
  FolderOpen,
  ClipboardCheck,
  Cpu,
  History,
  Settings,
  LogOut,
  ChevronRight,
  List,
  ListCollapse,
  ShieldCheck,
} from "lucide-react";
import { Tooltip } from "react-tooltip";

const SidebarItem = ({ item, onClick, isActive, isExpanded }) => (
  <div className="relative group">
    <button
      onClick={onClick}
      data-tooltip-id={!isExpanded ? "admin-sidebar-tooltip" : undefined}
      data-tooltip-content={item.label}
      style={
        isActive
          ? {
              background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
              backgroundColor: "#4f46e5",
              color: "#ffffff",
            }
          : undefined
      }
      className={`w-full flex items-center ${
        isExpanded ? "gap-3 px-3.5" : "justify-center px-2"
      } py-2.5 rounded-xl text-sm font-medium transition-all duration-150 cursor-pointer ${
        isActive
          ? "text-white shadow-md shadow-indigo-200"
          : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
      }`}
    >
      <item.icon className={`w-5 h-5 flex-shrink-0 ${isActive ? "text-white" : "text-slate-500 group-hover:text-slate-700"}`} />
      {isExpanded && <span className="truncate">{item.label}</span>}
      {isExpanded && isActive && (
        <span className="ml-auto w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
      )}
    </button>
  </div>
);

const AdminSidebar = ({ activeTab, setActiveTab }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);

  const navSections = [
    {
      title: "Overview",
      items: [
        { icon: LayoutDashboard, label: "Dashboard", id: "dashboard" },
      ],
    },
    {
      title: "Management",
      items: [
        { icon: Users, label: "Users & Roles", id: "users" },
        { icon: BookOpen, label: "Courses", id: "courses" },
        { icon: FolderOpen, label: "Content & Files", id: "content" },
        { icon: ClipboardCheck, label: "Quizzes", id: "quizzes" },
      ],
    },
    {
      title: "Intelligence",
      items: [
        { icon: Cpu, label: "LLM Quotas & Usage", id: "llm-usage" },
      ],
    },
    {
      title: "Platform",
      items: [
        { icon: History, label: "Audit Logs", id: "audit-logs" },
        { icon: Settings, label: "System Settings", id: "settings" },
      ],
    },
  ];

  return (
    <div
      className={`${
        isExpanded ? "w-64" : "w-20"
      } bg-white border-r border-slate-200 flex flex-col transition-all duration-300 relative z-30 select-none shadow-sm`}
    >
      {/* Header / Brand */}
      <div className="h-16 px-4 flex items-center justify-between border-b border-slate-100">
        <div
          className="flex items-center gap-2.5 cursor-pointer overflow-hidden"
          onClick={() => setActiveTab("dashboard")}
        >
          <LmsLogo size={36} />
          {isExpanded && (
            <div className="flex flex-col">
              <span className="font-bold text-slate-800 text-base leading-tight tracking-tight">
                LMS Admin
              </span>
              <span className="text-[10px] uppercase font-semibold text-indigo-600 tracking-wider flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" /> Console
              </span>
            </div>
          )}
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          title={isExpanded ? "Collapse Sidebar" : "Expand Sidebar"}
        >
          {isExpanded ? (
            <ListCollapse className="w-4 h-4" />
          ) : (
            <List className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Nav items */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-6 scrollbar-thin scrollbar-thumb-slate-200">
        {navSections.map((section, idx) => (
          <div key={idx} className="space-y-1">
            {isExpanded && (
              <div className="px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                {section.title}
              </div>
            )}
            {section.items.map((item) => (
              <SidebarItem
                key={item.id}
                item={item}
                isActive={activeTab === item.id || (activeTab === "user-detail" && item.id === "users")}
                isExpanded={isExpanded}
                onClick={() => setActiveTab(item.id)}
              />
            ))}
          </div>
        ))}
      </div>

      {/* Footer / Logout */}
      <div className="p-3 border-t border-slate-100">
        <button
          onClick={() => setIsLogoutModalOpen(true)}
          data-tooltip-id={!isExpanded ? "admin-sidebar-tooltip" : undefined}
          data-tooltip-content="Logout"
          className={`w-full flex items-center ${
            isExpanded ? "gap-3 px-3.5" : "justify-center px-2"
          } py-2.5 rounded-xl text-sm font-medium text-rose-600 hover:bg-rose-50 transition-colors`}
        >
          <LogOut className="w-5 h-5 flex-shrink-0" />
          {isExpanded && <span>Sign Out</span>}
        </button>
      </div>

      {/* Tooltip component for collapsed state */}
      {!isExpanded && (
        <Tooltip
          id="admin-sidebar-tooltip"
          place="right"
          className="!bg-slate-900 !text-white !text-xs !py-1.5 !px-3 !rounded-lg !shadow-xl z-50 font-medium"
        />
      )}

      <LogoutModal
        isOpen={isLogoutModalOpen}
        onClose={() => setIsLogoutModalOpen(false)}
        onConfirm={() => {
          setIsLogoutModalOpen(false);
          setActiveTab("logout");
        }}
      />
    </div>
  );
};

export default AdminSidebar;

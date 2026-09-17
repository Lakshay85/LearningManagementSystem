import { useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import AdminSidebar from "./AdminSidebar";
import AdminTopbar from "./AdminTopbar";
import AdminOverview from "./AdminOverview";
import UserManagement from "./UserManagement";
import UserDetail from "./UserDetail";
import CourseOversight from "./CourseOversight";
import ContentOversight from "./ContentOversight";
import QuizOversight from "./QuizOversight";
import LLMUsageDashboard from "./LLMUsageDashboard";
import AuditLogViewer from "./AuditLogViewer";
import SystemSettings from "./SystemSettings";
import NotificationSection from "../../components/NotificationSection";

function AdminDashboard() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [showNotifications, setShowNotifications] = useState(false);

  const handleTabChange = (tab) => {
    if (tab === "logout") {
      logout();
      return;
    }
    setActiveTab(tab);
  };

  const handleSelectUser = (id) => {
    setSelectedUserId(id);
    setActiveTab("user-detail");
  };

  const renderContent = () => {
    switch (activeTab) {
      case "users":
        return <UserManagement onSelectUser={handleSelectUser} />;
      case "user-detail":
        return (
          <UserDetail
            userId={selectedUserId}
            onBack={() => setActiveTab("users")}
          />
        );
      case "courses":
        return <CourseOversight />;
      case "content":
        return <ContentOversight />;
      case "quizzes":
        return <QuizOversight />;
      case "llm-usage":
        return <LLMUsageDashboard onSelectUser={handleSelectUser} />;
      case "audit-logs":
        return <AuditLogViewer />;
      case "settings":
        return <SystemSettings />;
      case "dashboard":
      default:
        return (
          <AdminOverview
            setActiveTab={setActiveTab}
            onSelectUser={handleSelectUser}
          />
        );
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-slate-800 antialiased overflow-hidden">
      {/* Sidebar */}
      <AdminSidebar activeTab={activeTab} setActiveTab={handleTabChange} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Topbar */}
        <AdminTopbar
          user={user}
          activeTab={activeTab}
          onToggleNotifications={() => setShowNotifications(true)}
        />

        {/* Scrollable Workspace */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          {renderContent()}
        </main>
      </div>

      {/* Notifications Drawer */}
      <NotificationSection
        isOpen={showNotifications}
        onClose={() => setShowNotifications(false)}
      />
    </div>
  );
}

export default AdminDashboard;

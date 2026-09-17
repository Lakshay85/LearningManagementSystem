import { useState, useEffect } from "react";
import { useAuth } from "../../hooks/useAuth";
import FacultySidebar from "./FacultySidebar";
import FacultyTopbar from "./FacultyTopbar";
import VideoUpload from "./VideoUpload";
import DashboardOverview from "./DashboardOverview";
import MyVideos from "./MyVideos";
import MyCourses from "./MyCourses";
import CourseCreate from "./CourseCreate";
import AllContent from "./AllContent";
import DraftsSection from "./DraftsSection";
import PublishedSection from "./PublishedSection";
import MyStudents from "./students/MyStudents";
import Analytics from "./analytics/Analytics";
import Settings from "./settings/Settings";
import NotificationSection from "../../components/NotificationSection";
import { applyThemeFonts } from "./settings/themeUtils";
import QuizManager from "./quiz/QuizManager";
import QuizBuilder from "./quiz/QuizBuilder";
import QuizSubmissions from "./quiz/QuizSubmissions";

function FacultyDashboard() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [editingCourse, setEditingCourse] = useState(null);
  const [editingQuizId, setEditingQuizId] = useState(null);
  const [viewingQuizId, setViewingQuizId] = useState(null);
  const [showNotifications, setShowNotifications] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem("faculty-theme") || "default");

  useEffect(() => {
    applyThemeFonts(theme);

    const handleThemeChange = () => {
      const newTheme = localStorage.getItem("faculty-theme") || "default";
      setTheme(newTheme);
      applyThemeFonts(newTheme);
    };

    window.addEventListener("faculty-theme-change", handleThemeChange);
    return () => {
      window.removeEventListener("faculty-theme-change", handleThemeChange);
    };
  }, [theme]);

  // Handle tab change with logout support
  const handleTabChange = (tab) => {
    if (tab === "logout") {
      logout();
      return;
    }
    setActiveTab(tab);
  };

  const renderContent = () => {
    switch (activeTab) {
      case "upload":
        return <VideoUpload />;
      case "videos":
        return <MyVideos setActiveTab={setActiveTab} />;
      case "quizzes":
        return (
          <QuizManager
            setActiveTab={setActiveTab}
            setEditingQuizId={setEditingQuizId}
            setViewingQuizId={setViewingQuizId}
          />
        );
      case "quiz-builder":
        return (
          <QuizBuilder
            quizId={editingQuizId}
            setActiveTab={setActiveTab}
            setViewingQuizId={setViewingQuizId}
          />
        );
      case "quiz-submissions":
        return (
          <QuizSubmissions
            quizId={viewingQuizId}
            setActiveTab={setActiveTab}
          />
        );
      case "courses":
        return (
          <MyCourses
            setActiveTab={setActiveTab}
            setEditingCourse={setEditingCourse}
          />
        );
      case "course-create":
        return (
          <CourseCreate
            setActiveTab={setActiveTab}
            editingCourse={editingCourse}
            setEditingCourse={setEditingCourse}
          />
        );
      case "all-content":
        return <AllContent setActiveTab={setActiveTab} />;
      case "drafts":
        return <DraftsSection />;
      case "published":
        return <PublishedSection />;
      case "students":
        return <MyStudents />;
      case "analytics":
        return <Analytics />;
      case "settings":
        return <Settings />;
      case "dashboard":
      default:
        return <DashboardOverview setActiveTab={setActiveTab} />;
    }
  };

  return (
    <div className={`flex h-screen theme-active theme-${theme}`}>
      <FacultySidebar activeTab={activeTab} setActiveTab={handleTabChange} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <FacultyTopbar
          user={user}
          onToggleNotifications={() => setShowNotifications(true)}
        />
        <div className="flex-1 overflow-y-auto p-8 bg-gray-50">
          {renderContent()}
        </div>
      </div>

      <NotificationSection
        isOpen={showNotifications}
        onClose={() => setShowNotifications(false)}
      />
    </div>
  );
}

export default FacultyDashboard;

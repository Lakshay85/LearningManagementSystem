import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../hooks/useAuth";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import MainSection from "./MainSection";
import AvailableCourses from "./AvailableCourses";
import CourseViewer from "./CourseViewer";
import StudentSetting from "./StudentSetting";
import StudentQuizHub from "./StudentQuizHub";
import NotificationSection from "../../components/NotificationSection";
import studentApi from "../../utils/studentApi";

function StudentDashboard() {
  const { user, logout } = useAuth();
  const [activeView, setActiveView] = useState("dashboard");
  const [enrolledCourses, setEnrolledCourses] = useState([]);
  const [selectedEnrolledCourse, setSelectedEnrolledCourse] = useState(null);
  const [loadingEnrolled, setLoadingEnrolled] = useState(true);
  const [showNotifications, setShowNotifications] = useState(false);

  // Fetch enrolled courses
  const fetchEnrolledCourses = useCallback(async () => {
    try {
      setLoadingEnrolled(true);
      const courses = await studentApi.getMyEnrolledCourses();
      setEnrolledCourses(courses || []);
    } catch (error) {
      console.error("Failed to fetch enrolled courses:", error);
    } finally {
      setLoadingEnrolled(false);
    }
  }, []);

  useEffect(() => {
    fetchEnrolledCourses();
  }, [fetchEnrolledCourses]);

  // Handle enrollment success - refresh enrolled courses
  const handleEnrollSuccess = useCallback(() => {
    fetchEnrolledCourses();
  }, [fetchEnrolledCourses]);

  // Handle viewing enrolled course
  const handleViewEnrolledCourse = useCallback((enrollment) => {
    setSelectedEnrolledCourse(enrollment);
    setActiveView("course-viewer");
  }, []);

  // Handle view change from sidebar
  const handleViewChange = useCallback(
    (view, data) => {
      // Handle logout
      if (view === "logout") {
        logout();
        return;
      }

      if (view === "enrolled-course" && data) {
        handleViewEnrolledCourse(data);
      } else {
        setActiveView(view);
        setSelectedEnrolledCourse(null);
      }
    },
    [handleViewEnrolledCourse, logout]
  );

  // Handle back from course viewer
  const handleBackFromCourseViewer = useCallback(() => {
    setSelectedEnrolledCourse(null);
    setActiveView("courses");
  }, []);

  const renderContent = () => {
    switch (activeView) {
      case "courses":
        return <AvailableCourses onEnrollSuccess={handleEnrollSuccess} />;
      case "settings":
        return <StudentSetting />;
      case "quiz":
        return <StudentQuizHub />;
      case "course-viewer":
        return selectedEnrolledCourse ? (
          <CourseViewer
            course={selectedEnrolledCourse}
            onBack={handleBackFromCourseViewer}
          />
        ) : (
          <AvailableCourses onEnrollSuccess={handleEnrollSuccess} />
        );
      case "dashboard":
      default:
        return <MainSection onToggleNotifications={() => setShowNotifications(true)} />;
    }
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#f8fafc] text-[#1e293b] transition-colors duration-200 font-sans">
      <Sidebar
        activeView={activeView}
        onViewChange={handleViewChange}
        enrolledCourses={enrolledCourses}
        loadingEnrolled={loadingEnrolled}
        selectedCourseId={
          selectedEnrolledCourse?.courseId || selectedEnrolledCourse?.id
        }
        user={user}
      />
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {activeView !== "dashboard" && (
          <Topbar onViewChange={handleViewChange} user={user} />
        )}
        <main
          className={`flex-1 overflow-y-auto no-scrollbar ${activeView === "course-viewer" ? "" : "p-6 md:p-10"
            }`}
        >
          {renderContent()}
        </main>
      </div>

      <NotificationSection
        isOpen={showNotifications}
        onClose={() => setShowNotifications(false)}
      />
    </div>
  );
}

export default StudentDashboard;

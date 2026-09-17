import { useState } from "react";
import LogoutModal from "../../components/common/LogoutModal";
import LmsLogo from "../../components/common/LmsLogo";

const Sidebar = ({
  activeView = "dashboard",
  onViewChange = () => { },
  enrolledCourses = [],
  loadingEnrolled = false,
  selectedCourseId = null,
  user = null,
}) => {
  const [myCoursesOpen, setMyCoursesOpen] = useState(true);
  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);


  const menuItems = [
    { icon: "dashboard", label: "Dashboard", view: "dashboard" },
    { icon: "explore", label: "Browse Courses", view: "courses" },
    { icon: "quiz", label: "Quiz", view: "quiz" },
  ];

  // Get course category color
  const getCategoryColor = (category) => {
    const colors = {
      programming: "bg-blue-500",
      web_development: "bg-purple-500",
      mobile_development: "bg-green-500",
      data_science: "bg-orange-500",
      machine_learning: "bg-red-500",
      design: "bg-pink-500",
      business: "bg-yellow-500",
      marketing: "bg-teal-500",
      academics: "bg-indigo-500",
      other: "bg-gray-500",
    };
    return colors[category] || "bg-indigo-500";
  };

  return (
    <aside className="hidden md:flex flex-col w-72 bg-white border-r border-slate-200 p-6 flex-shrink-0 z-20 h-full">
      <div
        onClick={() => onViewChange("dashboard")}
        className="flex items-center gap-3 mb-10 px-2 cursor-pointer group"
      >
        <LmsLogo size={38} className="transition-transform group-hover:scale-105" />
        <span className="text-xl font-bold tracking-tight text-slate-900 group-hover:text-indigo-600 transition-colors">
          LMS Enterprise
        </span>
      </div>
      {/* Scrollable Menu Section */}
      <div className="flex-1 overflow-y-auto px-2 pb-4">
        {/* Main Menu */}
        <div className="flex flex-col gap-1.5 mb-6">
          {menuItems.map((item) => (
            <div
              key={item.view}
              onClick={() => onViewChange(item.view)}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-all group ${activeView === item.view
                ? "bg-[#6366f1] text-white shadow-md shadow-indigo-500/25"
                : "text-slate-500 hover:bg-slate-50"
                }`}
            >
              <span
                className={`material-symbols-outlined ${activeView === item.view
                  ? ""
                  : "group-hover:text-[#6366f1] transition-colors"
                  }`}
                style={{
                  fontVariationSettings:
                    activeView === item.view ? '"FILL" 1' : '"FILL" 0',
                }}
              >
                {item.icon}
              </span>
              <span className="text-sm font-medium">{item.label}</span>
            </div>
          ))}
        </div>

        {/* My Enrolled Courses Section */}
        <div className="mb-6">
          <button
            onClick={() => setMyCoursesOpen(!myCoursesOpen)}
            className="flex items-center justify-between w-full text-sm font-medium text-slate-500 mb-3 px-2 hover:text-slate-700 transition-colors"
          >
            <span>My Courses</span>
            <span className="material-symbols-outlined text-lg">
              {myCoursesOpen ? "expand_less" : "expand_more"}
            </span>
          </button>

          {myCoursesOpen && (
            <div className="space-y-1">
              {loadingEnrolled ? (
                <div className="flex items-center justify-center py-4">
                  <span className="material-symbols-outlined animate-spin text-slate-400 text-xl">
                    progress_activity
                  </span>
                </div>
              ) : enrolledCourses.length === 0 ? (
                <div className="text-center py-4 px-2">
                  <div className="size-12 rounded-full bg-slate-50 flex items-center justify-center mx-auto mb-2">
                    <span className="material-symbols-outlined text-slate-300 text-2xl">
                      school
                    </span>
                  </div>
                  <p className="text-sm text-slate-400 mb-2">
                    No enrolled courses
                  </p>
                  <button
                    onClick={() => onViewChange("courses")}
                    className="text-xs text-[#6366f1] hover:text-[#4f46e5] font-medium transition-colors"
                  >
                    Browse courses
                  </button>
                </div>
              ) : (
                enrolledCourses.map((enrollment) => {
                  const course = enrollment.course;
                  const isSelected =
                    selectedCourseId === enrollment.courseId ||
                    selectedCourseId === course?.id;
                  return (
                    <button
                      key={enrollment.id}
                      onClick={() =>
                        onViewChange("enrolled-course", enrollment)
                      }
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${isSelected
                        ? "bg-[#6366f1]/10 border border-[#6366f1]/20"
                        : "hover:bg-slate-50"
                        }`}
                    >
                      <div
                        className={`w-8 h-8 rounded-lg ${getCategoryColor(
                          course?.category
                        )} flex items-center justify-center flex-shrink-0 shadow-sm`}
                      >
                        <span className="material-symbols-outlined text-white text-lg">
                          play_circle
                        </span>
                      </div>
                      <div className="flex-1 min-w-0 text-left">
                        <p
                          className={`text-sm font-medium truncate ${isSelected ? "text-[#6366f1]" : "text-slate-700"
                            }`}
                        >
                          {course?.title || "Untitled Course"}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <div className="w-16 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-[#6366f1] rounded-full transition-all"
                              style={{
                                width: `${parseFloat(enrollment.progress) || 0
                                  }%`,
                              }}
                            />
                          </div>
                          <span className="text-xs text-slate-400 font-medium">
                            {parseFloat(enrollment.progress)?.toFixed(0) || 0}%
                          </span>
                        </div>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          )}
        </div>
      </div>{" "}
      <div className="mt-auto pt-6">
        <div className="flex items-center gap-3 px-2">
          {/* User Avatar */}
          <div
            className="bg-center bg-no-repeat bg-cover rounded-full size-11 ring-2 ring-slate-100 bg-slate-200 flex items-center justify-center overflow-hidden"
          >
            {user?.profilePictureUrl ? (
              <img src={user.profilePictureUrl} alt={user.firstName} className="w-full h-full object-cover" />
            ) : (
              <span className="text-lg font-bold text-slate-500">
                {user?.firstName?.charAt(0) || "U"}
              </span>
            )}
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-sm font-bold text-slate-900 truncate">
              {user?.firstName ? `${user.firstName} ${user.lastName || ""}` : "User"}
            </span>
            <span className="text-xs text-slate-500 truncate">{user?.role || "Student"}</span>
          </div>
          <div className="ml-auto flex items-center gap-1">
            <button
              onClick={() => onViewChange("settings")}
              className="text-slate-400 hover:text-slate-900 transition-colors p-1.5 rounded-lg hover:bg-slate-100"
              title="Settings"
            >
              <span className="material-symbols-outlined text-[20px]">settings</span>
            </button>
            <button
              onClick={() => setIsLogoutModalOpen(true)}
              className="text-slate-400 hover:text-red-600 transition-colors p-1.5 rounded-lg hover:bg-red-50"
              title="Logout"
            >
              <span className="material-symbols-outlined text-[20px]">logout</span>
            </button>
          </div>
        </div>
      </div>
      <LogoutModal
        isOpen={isLogoutModalOpen}
        onClose={() => setIsLogoutModalOpen(false)}
        onConfirm={() => {
          setIsLogoutModalOpen(false);
          onViewChange("logout");
        }}
      />
    </aside>
  );
};

export default Sidebar;

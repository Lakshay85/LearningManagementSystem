import { useState } from "react";
import LogoutModal from "../../components/common/LogoutModal";
import LmsLogo from "../../components/common/LmsLogo";
import {
  LayoutDashboard,
  Video,
  BookOpen,
  Users,
  FileText,
  Settings,
  ChevronDown,
  ChevronUp,
  Upload,
  FolderOpen,
  BarChart3,
  LogOut,
  Search,
  ChevronRight,
  List,
  ListCollapse,
  ClipboardCheck,
} from "lucide-react";
import { Tooltip } from "react-tooltip";

const SidebarItem = ({ item, onClick, isActive, isExpanded }) => (
  <div className="relative group">
    <button
      onClick={onClick}
      data-tooltip-id={!isExpanded ? "sidebar-tooltip" : undefined}
      data-tooltip-content={item.label}
      className={`w-full flex items-center ${isExpanded ? "gap-3 px-3" : "justify-center px-2"} py-2.5 rounded-lg text-sm transition-colors ${isActive
        ? "bg-emerald-50 text-emerald-700 font-medium"
        : "text-gray-600 hover:bg-gray-100"
        }`}
    >
      <item.icon className="w-5 h-5 flex-shrink-0" />
      {isExpanded && <span className="truncate">{item.label}</span>}
    </button>
  </div>
);

/**
 * Sidebar Component with Minimize/Maximize functionality
 */
const FacultySidebar = ({ activeTab, setActiveTab }) => {
  const [mainMenuOpen, setMainMenuOpen] = useState(true);
  const [contentMenuOpen, setContentMenuOpen] = useState(true);
  const [isExpanded, setIsExpanded] = useState(true);
  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);

  const mainMenuItems = [
    { icon: LayoutDashboard, label: "Dashboard", id: "dashboard" },
    { icon: Upload, label: "Upload Video", id: "upload" },
    { icon: Video, label: "My Videos", id: "videos" },
    { icon: BookOpen, label: "Courses", id: "courses" },
    { icon: ClipboardCheck, label: "Quizzes", id: "quizzes" },
    { icon: Users, label: "Students", id: "students" },
    { icon: BarChart3, label: "Analytics", id: "analytics" },
  ];

  const contentItems = [
    { icon: FolderOpen, label: "All Content", id: "all-content" },
    { icon: FileText, label: "Drafts", id: "drafts" },
    { icon: Video, label: "Published", id: "published" },
  ];

  const handleNavigation = (tabId) => {
    if (tabId === "logout") {
      setIsLogoutModalOpen(true);
      return;
    }
    setActiveTab(tabId);
    if (!isExpanded) {
      setIsExpanded(true);
    }
  };

  const handleConfirmLogout = () => {
    setActiveTab("logout");
    setIsLogoutModalOpen(false);
  };

  return (
    <div
      className={`${isExpanded ? "w-72" : "w-20"
        } h-screen bg-gray-50 border-r border-gray-200 flex flex-col transition-all duration-300 relative z-50`}
    >
      {/* User Profile Section with Toggle */}
      <div className={`${isExpanded ? "p-4" : "p-2"} border-b border-gray-200 transition-all duration-300`}>
        <div className={`flex items-center ${isExpanded ? "justify-between" : "flex-row-reverse justify-center gap-1"}`}>
          {/* Logo Container */}
          <div className={`flex items-center gap-3 overflow-hidden ${!isExpanded && "justify-center"}`}>
            <LmsLogo size={isExpanded ? 38 : 32} className="transition-all duration-300" />
            {isExpanded && (
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-gray-900 truncate">LMS Enterprise</h3>
                <p className="text-xs text-gray-500 truncate font-medium">Faculty Portal</p>
              </div>
            )}
          </div>

          {/* Toggle Button - Only visible when expanded */}
          {isExpanded && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-gray-500 hover:bg-gray-100 p-1.5 rounded-lg transition-colors"
              data-tooltip-id="sidebar-tooltip"
              data-tooltip-content="Collapse Sidebar"
            >
              <ListCollapse className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Scrollable Menu Section */}
      <div className="mt-2 flex-1 overflow-y-auto px-4 pb-4 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:'none'] [scrollbar-width:'none']">
        {/* Main Menu */}
        <div className="mb-6">
          {isExpanded ? (
            <button
              onClick={() => setMainMenuOpen(!mainMenuOpen)}
              className="flex items-center justify-between w-full text-sm font-medium text-gray-500 mb-3"
            >
              <span>Main Menu</span>
              {mainMenuOpen ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
          ) : (
            <div className="h-4"></div> // Spacer when collapsed
          )}

          {(mainMenuOpen || !isExpanded) && (
            <nav className="space-y-1">
              {mainMenuItems.map((item) => (
                <SidebarItem
                  key={item.id}
                  item={item}
                  isActive={activeTab === item.id}
                  isExpanded={isExpanded}
                  onClick={() => handleNavigation(item.id)}
                />
              ))}
            </nav>
          )}
        </div>

        {/* Content Menu */}
        <div className="mb-6">
          {isExpanded ? (
            <button
              onClick={() => setContentMenuOpen(!contentMenuOpen)}
              className="flex items-center justify-between w-full text-sm font-medium text-gray-500 mb-3"
            >
              <span>Content</span>
              {contentMenuOpen ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
          ) : (
            <div className="border-t border-gray-200 my-4"></div> // Separator when collapsed
          )}

          {(contentMenuOpen || !isExpanded) && (
            <nav className="space-y-1">
              {contentItems.map((item) => (
                <SidebarItem
                  key={item.id}
                  item={item}
                  isActive={activeTab === item.id}
                  isExpanded={isExpanded}
                  onClick={() => handleNavigation(item.id)}
                />
              ))}
            </nav>
          )}
        </div>
      </div>

      {/* Bottom Section */}
      <div className="p-4 border-t border-gray-200 space-y-2">
        <SidebarItem
          item={{ icon: Settings, label: "Settings" }}
          isActive={activeTab === "settings"}
          isExpanded={isExpanded}
          onClick={() => handleNavigation("settings")}
        />
        <SidebarItem
          item={{ icon: LogOut, label: "Logout" }}
          isActive={activeTab === "logout"}
          isExpanded={isExpanded}
          onClick={() => handleNavigation("logout")}
        />
      </div>

      {/* React Tooltip Component */}
      <Tooltip
        id="sidebar-tooltip"
        place="right"
        className="z-[100] !bg-gray-800 !text-white !text-xs !px-2 !py-1 !rounded !opacity-100"
        border="1px solid transparent"
      />
      <LogoutModal
        isOpen={isLogoutModalOpen}
        onClose={() => setIsLogoutModalOpen(false)}
        onConfirm={handleConfirmLogout}
      />
    </div>
  );
};

export default FacultySidebar;

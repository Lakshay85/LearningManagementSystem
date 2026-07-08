import { useState } from "react";
import {
  Search,
  MessageSquare,
  Bell,
  ChevronDown,
  Settings,
  LogOut,
} from "lucide-react";

const Topbar = ({ onViewChange, user }) => {
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  const handleLogout = () => {
    onViewChange("logout");
  };

  return (
    <div className="bg-white border-b border-gray-200 px-8 py-4">
      <div className="flex items-center justify-between">
        {/* Left Section - Title and Greeting */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Courses Dashboard
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Hello {user?.firstName || "Student"}, welcome back!
          </p>
        </div>

        {/* Right Section - Search and Icons */}
        <div className="flex items-center gap-6">
          {/* Search Bar */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search Dashboard"
              className="w-80 pl-10 pr-12 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <Search className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" />
            <button className="absolute right-3 top-2.5">
              <svg
                className="w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
                />
              </svg>
            </button>
          </div>

          {/* Message Icon */}
          <button className="relative p-2 hover:bg-gray-100 rounded-lg transition">
            <MessageSquare className="w-6 h-6 text-gray-600" />
          </button>

          {/* Notification Icon */}
          <button className="relative p-2 hover:bg-gray-100 rounded-lg transition">
            <Bell className="w-6 h-6 text-gray-600" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          {/* User Profile */}
          <div className="relative">
            <button
              onClick={() => setShowProfileMenu(!showProfileMenu)}
              className="flex items-center gap-2 hover:bg-gray-100 rounded-lg p-2 transition"
            >
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
                <span className="text-white font-semibold">
                  {user?.firstName?.[0] || "S"}
                  {user?.lastName?.[0] || "T"}
                </span>
              </div>
              <ChevronDown className="w-4 h-4 text-gray-600" />
            </button>

            {/* Dropdown Menu */}
            {showProfileMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
                <div className="px-4 py-2 border-b border-gray-200">
                  <p className="font-semibold text-gray-900">
                    {user?.firstName} {user?.lastName}
                  </p>
                  <p className="text-sm text-gray-500">{user?.email}</p>
                </div>
                <button
                  onClick={() => onViewChange("settings")}
                  className="w-full flex items-center gap-3 px-4 py-2 hover:bg-gray-100 text-left"
                >
                  <Settings className="w-4 h-4 text-gray-600" />
                  <span className="text-sm text-gray-700">Settings</span>
                </button>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-2 hover:bg-gray-100 text-left"
                >
                  <LogOut className="w-4 h-4 text-gray-600" />
                  <span className="text-sm text-gray-700">Logout</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Topbar;

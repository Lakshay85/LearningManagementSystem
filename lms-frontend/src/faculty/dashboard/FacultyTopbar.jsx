import { useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import {
  Search,
  MessageSquare,
  Bell,
  ChevronDown,
  Settings,
  LogOut,
} from "lucide-react";

const FacultyTopbar = ({ user, onToggleNotifications }) => {
  const { logout } = useAuth();
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  return (
    <div className="bg-white border-b border-gray-200 px-8 py-4">
      <div className="flex items-center justify-between">
        {/* Left Section - Title and Greeting */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Faculty Dashboard
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Hello {user?.firstName || "Professor"}, welcome back!
          </p>
        </div>

        {/* Right Section - Search and Icons */}
        <div className="flex items-center gap-6">
          {/* Search Bar */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search content..."
              className="w-80 pl-10 pr-12 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
            <Search className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" />
          </div>

          {/* Message Icon
          <button className="relative p-2 hover:bg-gray-100 rounded-lg transition">
            <MessageSquare className="w-6 h-6 text-gray-600" />
          </button> */}

          {/* Notification Icon */}
          <button
            onClick={onToggleNotifications}
            className="relative p-2 hover:bg-gray-100 rounded-lg transition"
          >
            <Bell className="w-6 h-6 text-gray-600" />
            {/* <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span> */}
          </button>

          {/* User Profile */}
          <div className="relative">
            <button
              onClick={() => setShowProfileMenu(!showProfileMenu)}
              className="flex items-center gap-2 hover:bg-gray-100 rounded-lg p-2 transition"
            >
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-full flex items-center justify-center">
                <span className="text-white font-semibold">
                  {user?.firstName?.[0] || "F"}
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
                <button className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2">
                  <Settings className="w-4 h-4" />
                  Settings
                </button>
                <button
                  onClick={logout}
                  className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FacultyTopbar;

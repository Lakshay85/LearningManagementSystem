import { useState } from "react";
import { User, Lock, Trash2 } from "lucide-react";
import ProfileSettings from "./settings/ProfileSettings";
import PasswordSettings from "./settings/PasswordSettings";
import DangerZone from "./settings/DangerZone";

const StudentSetting = () => {
  const [activeTab, setActiveTab] = useState("profile");

  const menuItems = [
    { id: "profile", label: "Profile", icon: User },
    { id: "password", label: "Password", icon: Lock },
    { id: "danger", label: "Danger Zone", icon: Trash2, className: "text-red-600 hover:bg-red-50" },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case "profile":
        return <ProfileSettings />;
      case "password":
        return <PasswordSettings />;
      case "danger":
        return <DangerZone />;
      default:
        return <ProfileSettings />;
    }
  };

  return (
    <div className="max-w-7xl mx-auto font-sans">
      {/* Header */}
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Settings</h1>
        <p className="text-slate-500 mt-1">
          Manage your account settings and preferences.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Sidebar Navigation */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-[2rem] p-4 shadow-sm border border-slate-100 sticky top-6">
            <nav className="space-y-1">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;

                // Base classes for all items
                let buttonClasses = "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ";

                // Active vs Inactive logic
                if (isActive) {
                  if (item.id === "danger") {
                    buttonClasses += "bg-red-50 text-red-600 shadow-sm ring-1 ring-red-100";
                  } else {
                    buttonClasses += "bg-indigo-600 text-white shadow-md shadow-indigo-500/20";
                  }
                } else {
                  if (item.id === "danger") {
                    buttonClasses += "text-red-500 hover:bg-red-50";
                  } else {
                    buttonClasses += "text-slate-500 hover:bg-slate-50 hover:text-slate-900";
                  }
                }

                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={buttonClasses}
                  >
                    <Icon className={`size-5 ${isActive ? "" : "opacity-70"}`} />
                    {item.label}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Content Area */}
        <div className="lg:col-span-3">
          {renderContent()}
        </div>
      </div>
      <div className="h-10"></div>
    </div>
  );
};

export default StudentSetting;

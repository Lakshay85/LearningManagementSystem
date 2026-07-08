import { useState } from "react";
import ProfileSettings from "./ProfileSettings";
import SecuritySettings from "./SecuritySettings";
import AccountSettings from "./AccountSettings";
import { User, Lock, Shield } from "lucide-react";

const Settings = () => {
    const [activeTab, setActiveTab] = useState("profile");

    const tabs = [
        { id: "profile", label: "Profile", icon: User },
        { id: "security", label: "Security", icon: Lock },
        { id: "account", label: "Account", icon: Shield },
    ];

    const renderContent = () => {
        switch (activeTab) {
            case "profile":
                return <ProfileSettings />;
            case "security":
                return <SecuritySettings />;
            case "account":
                return <AccountSettings />;
            default:
                return <ProfileSettings />;
        }
    };

    return (
        <div className="max-w-6xl mx-auto">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
                <p className="text-gray-500 mt-1">
                    Manage your account settings and preferences
                </p>
            </div>

            <div className="flex flex-col lg:flex-row gap-8">
                {/* Sidebar Navigation */}
                <div className="w-full lg:w-64 flex-shrink-0">
                    <nav className="space-y-1">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === tab.id
                                        ? "bg-emerald-50 text-emerald-700"
                                        : "text-gray-600 hover:bg-gray-50"
                                    }`}
                            >
                                <tab.icon className="w-5 h-5" />
                                {tab.label}
                            </button>
                        ))}
                    </nav>
                </div>

                {/* Main Content Area */}
                <div className="flex-1 min-w-0">
                    {renderContent()}
                </div>
            </div>
        </div>
    );
};

export default Settings;

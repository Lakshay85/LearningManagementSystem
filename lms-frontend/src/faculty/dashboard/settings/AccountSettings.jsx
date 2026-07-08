import { useState } from "react";
import { Trash2, AlertTriangle, Loader2 } from "lucide-react";
import { useAuth } from "../../../hooks/useAuth";
import facultyApi from "../../../utils/facultyApi";

const AccountSettings = () => {
    const { logout } = useAuth();
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [loading, setLoading] = useState(false);
    const [confirmText, setConfirmText] = useState("");

    const handleDeleteAccount = async () => {
        if (confirmText !== "DELETE") return;

        setLoading(true);
        try {
            await facultyApi.deleteAccount();

            // Logout user (will redirect to login page)
            logout();
        } catch (error) {
            console.error("Failed to delete account", error);
            alert(error.response?.data?.message || error.message || "Failed to delete account");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-2xl">
            <div className="mb-8">
                <h2 className="text-xl font-semibold text-gray-900">Account Settings</h2>
                <p className="text-sm text-gray-500 mt-1">
                    Manage your account status and data
                </p>
            </div>

            <div className="bg-red-50 border border-red-200 rounded-xl p-6">
                <div className="flex items-start gap-4">
                    <div className="p-2 bg-red-100 rounded-lg">
                        <AlertTriangle className="w-6 h-6 text-red-600" />
                    </div>
                    <div className="flex-1">
                        <h3 className="text-lg font-semibold text-red-900">Delete Account</h3>
                        <p className="text-red-700 mt-1 text-sm">
                            Once you delete your account, there is no going back. Please be certain.
                            All your uploaded videos, documents, and data will be permanently deleted.
                        </p>

                        {!showDeleteConfirm ? (
                            <button
                                onClick={() => setShowDeleteConfirm(true)}
                                className="mt-4 flex items-center gap-2 bg-white border border-red-300 text-red-600 px-4 py-2 rounded-lg hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition"
                            >
                                <Trash2 className="w-4 h-4" />
                                Delete Account
                            </button>
                        ) : (
                            <div className="mt-6 bg-white p-4 rounded-lg border border-red-200">
                                <p className="text-sm font-medium text-gray-900 mb-3">
                                    Type <span className="font-bold font-mono">DELETE</span> to confirm
                                </p>
                                <div className="flex gap-3">
                                    <input
                                        type="text"
                                        value={confirmText}
                                        onChange={(e) => setConfirmText(e.target.value)}
                                        placeholder="DELETE"
                                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                                    />
                                    <button
                                        onClick={handleDeleteAccount}
                                        disabled={confirmText !== "DELETE" || loading}
                                        className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                    >
                                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Confirm Deletion"}
                                    </button>
                                    <button
                                        onClick={() => {
                                            setShowDeleteConfirm(false);
                                            setConfirmText("");
                                        }}
                                        disabled={loading}
                                        className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AccountSettings;

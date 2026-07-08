import { useState } from "react";
import authApi from "../../../utils/authApi";

const DangerZone = () => {
    const [deleteConfirmation, setDeleteConfirmation] = useState("");
    const [loading, setLoading] = useState(false);

    const handleDeleteAccount = async () => {
        if (deleteConfirmation !== "DELETE") {
            alert("Please type 'DELETE' to confirm account deletion");
            return;
        }

        if (
            !window.confirm(
                "Are you absolutely sure you want to permanently delete your account? This action cannot be undone."
            )
        ) {
            return;
        }

        setLoading(true);
        try {
            await authApi.deleteAccount();
            alert("Account deleted successfully. You will be logged out.");
            window.location.href = "/login";
        } catch (error) {
            console.error("Failed to delete account:", error);
            alert("Failed to delete account. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white rounded-[2.5rem] p-8 shadow-sm border border-slate-100">
            <div className="mb-8">
                <h3 className="text-xl font-bold text-red-600">Danger Zone</h3>
                <p className="text-sm text-slate-500 mt-1">Irreversible and destructive actions.</p>
            </div>

            <div className="p-6 bg-red-50 rounded-2xl border border-red-100">
                <h4 className="font-bold text-red-900 mb-2">Delete Account</h4>
                <p className="text-sm text-red-700/80 mb-6 leading-relaxed max-w-2xl">
                    Once you delete your account, there is no going back. All your data, progress, and certificates will be permanently removed from our servers.
                </p>

                <div className="space-y-4 max-w-md">
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-red-800 uppercase tracking-wider ml-1">
                            Confirmation
                        </label>
                        <input
                            type="text"
                            value={deleteConfirmation}
                            onChange={(e) => setDeleteConfirmation(e.target.value)}
                            className="w-full px-4 py-3 rounded-xl bg-white border border-red-200 text-red-900 focus:ring-2 focus:ring-red-500/20 focus:border-red-300 transition-all outline-none placeholder:text-red-300"
                            placeholder="Type 'DELETE' to confirm"
                        />
                    </div>

                    <button
                        onClick={handleDeleteAccount}
                        disabled={loading || deleteConfirmation !== "DELETE"}
                        className="w-full px-6 py-3 bg-red-600 text-white font-bold rounded-xl hover:bg-red-700 transition-colors shadow-lg shadow-red-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {loading ? "Deleting..." : "Delete Account Permanently"}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default DangerZone;

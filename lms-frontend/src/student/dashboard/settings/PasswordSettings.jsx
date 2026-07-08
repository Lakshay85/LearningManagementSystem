import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import authApi from "../../../utils/authApi";

const PasswordSettings = () => {
    const [loading, setLoading] = useState(false);
    const [showCurrentPassword, setShowCurrentPassword] = useState(false);
    const [showNewPassword, setShowNewPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    const [passwordData, setPasswordData] = useState({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
    });

    const handlePasswordChange = async (e) => {
        e.preventDefault();
        if (
            !passwordData.currentPassword ||
            !passwordData.newPassword ||
            !passwordData.confirmPassword
        ) {
            alert("Please fill in all password fields");
            return;
        }

        if (passwordData.newPassword !== passwordData.confirmPassword) {
            alert("New passwords do not match");
            return;
        }

        if (passwordData.newPassword.length < 6) {
            alert("New password must be at least 6 characters long");
            return;
        }

        setLoading(true);
        try {
            await authApi.updatePassword({
                currentPassword: passwordData.currentPassword,
                newPassword: passwordData.newPassword,
            });
            alert("Password changed successfully!");
            setPasswordData({
                currentPassword: "",
                newPassword: "",
                confirmPassword: "",
            });
        } catch (error) {
            console.error("Failed to change password:", error);
            alert("Failed to change password. Please check your current password.");
        } finally {
            setLoading(false);
        }
    };

    const InputField = ({ label, value, onChange, show, toggleShow, placeholder }) => (
        <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700 ml-1">
                {label}
            </label>
            <div className="relative">
                <input
                    type={show ? "text" : "password"}
                    value={value}
                    onChange={onChange}
                    className="w-full px-4 py-3 pr-12 rounded-xl bg-slate-50 border-none text-slate-900 focus:ring-2 focus:ring-indigo-500/20 focus:bg-white transition-all outline-none"
                    placeholder={placeholder}
                    required
                />
                <button
                    type="button"
                    onClick={toggleShow}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                >
                    {show ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
                </button>
            </div>
        </div>
    );

    return (
        <div className="bg-white rounded-[2.5rem] p-8 shadow-sm border border-slate-100">
            <div className="mb-8">
                <h3 className="text-xl font-bold text-slate-900">Security</h3>
                <p className="text-sm text-slate-500 mt-1">Manage your password and security preferences.</p>
            </div>

            <form onSubmit={handlePasswordChange} className="space-y-6 max-w-xl">
                <InputField
                    label="Current Password"
                    value={passwordData.currentPassword}
                    onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
                    show={showCurrentPassword}
                    toggleShow={() => setShowCurrentPassword(!showCurrentPassword)}
                    placeholder="Enter current password"
                />

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <InputField
                        label="New Password"
                        value={passwordData.newPassword}
                        onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                        show={showNewPassword}
                        toggleShow={() => setShowNewPassword(!showNewPassword)}
                        placeholder="Min. 6 characters"
                    />

                    <InputField
                        label="Confirm Password"
                        value={passwordData.confirmPassword}
                        onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                        show={showConfirmPassword}
                        toggleShow={() => setShowConfirmPassword(!showConfirmPassword)}
                        placeholder="Re-enter new password"
                    />
                </div>

                <div className="pt-4">
                    <button
                        type="submit"
                        disabled={loading}
                        className="px-8 py-3 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-500/30 disabled:opacity-70 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {loading ? (
                            <>
                                <span className="size-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                                <span>Updating...</span>
                            </>
                        ) : (
                            "Update Password"
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default PasswordSettings;

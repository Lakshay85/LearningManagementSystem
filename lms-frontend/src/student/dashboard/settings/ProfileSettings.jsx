import { useState } from "react";
import studentApi from "../../../utils/studentApi";

const ProfileSettings = () => {
    const [loading, setLoading] = useState(false);
    const [profileData, setProfileData] = useState({
        firstName: "",
        lastName: "",
    });

    const handleProfileUpdate = async (e) => {
        e.preventDefault();
        if (!profileData.firstName.trim() || !profileData.lastName.trim()) {
            // You might want to use a toast notification here ideally
            alert("Please fill in all fields");
            return;
        }

        setLoading(true);
        try {
            await studentApi.updateProfile({
                firstName: profileData.firstName.trim(),
                lastName: profileData.lastName.trim(),
            });
            alert("Profile updated successfully!");
            setProfileData({ firstName: "", lastName: "" });
        } catch (error) {
            console.error("Failed to update profile:", error);
            alert("Failed to update profile. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white rounded-[2.5rem] p-8 shadow-sm border border-slate-100">
            <div className="mb-8">
                <h3 className="text-xl font-bold text-slate-900">Personal Information</h3>
                <p className="text-sm text-slate-500 mt-1">Update your personal details here.</p>
            </div>

            <form onSubmit={handleProfileUpdate} className="space-y-6 max-w-xl">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-slate-700 ml-1">
                            First Name
                        </label>
                        <input
                            type="text"
                            value={profileData.firstName}
                            onChange={(e) =>
                                setProfileData({
                                    ...profileData,
                                    firstName: e.target.value,
                                })
                            }
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 border-none text-slate-900 focus:ring-2 focus:ring-indigo-500/20 focus:bg-white transition-all outline-none"
                            placeholder="e.g. Alex"
                            required
                        />
                    </div>
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-slate-700 ml-1">
                            Last Name
                        </label>
                        <input
                            type="text"
                            value={profileData.lastName}
                            onChange={(e) =>
                                setProfileData({ ...profileData, lastName: e.target.value })
                            }
                            className="w-full px-4 py-3 rounded-xl bg-slate-50 border-none text-slate-900 focus:ring-2 focus:ring-indigo-500/20 focus:bg-white transition-all outline-none"
                            placeholder="e.g. Johnson"
                            required
                        />
                    </div>
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
                            "Save Changes"
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default ProfileSettings;

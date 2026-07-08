import { useState, useEffect } from "react";
import { Camera, Save, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import { useAuth } from "../../../hooks/useAuth";
import facultyApi from "../../../utils/facultyApi";

const ProfileSettings = () => {
    const { user: authUser, refreshUser } = useAuth();
    const [formData, setFormData] = useState({
        firstName: "",
        lastName: "",
        email: "",
        profilePicture: "",
    });
    const [isLoading, setIsLoading] = useState(false);
    const [imagePreview, setImagePreview] = useState(null);
    const [imageFile, setImageFile] = useState(null);
    const [message, setMessage] = useState({ type: "", content: "" });

    useEffect(() => {
        if (authUser) {
            setFormData({
                firstName: authUser.firstName || "",
                lastName: authUser.lastName || "",
                email: authUser.email || "",
                profilePicture: authUser.profilePictureUrl || "",
            });
            setImagePreview(authUser.profilePictureUrl);
        }
    }, [authUser]);

    const handleImageChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            // Validate file size (e.g. 5MB)
            if (file.size > 5 * 1024 * 1024) {
                setMessage({ type: "error", content: "Image size must be less than 5MB" });
                return;
            }

            setImageFile(file);
            const reader = new FileReader();
            reader.onloadend = () => {
                setImagePreview(reader.result);
            };
            reader.readAsDataURL(file);
            setMessage({ type: "", content: "" });
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setMessage({ type: "", content: "" });

        try {
            let profileUpdated = false;

            // 1. Update Profile Info if changed
            if (formData.firstName !== authUser?.firstName || formData.lastName !== authUser?.lastName) {
                await facultyApi.updateProfile({
                    firstName: formData.firstName,
                    lastName: formData.lastName
                });
                profileUpdated = true;
            }

            // 2. Upload Image if changed
            if (imageFile) {
                const formDataUpload = new FormData();
                formDataUpload.append("file", imageFile);
                await facultyApi.uploadProfilePicture(formDataUpload);
                profileUpdated = true;
            }

            if (profileUpdated) {
                // Refresh user data from backend
                await refreshUser();
                setMessage({ type: "success", content: "Profile updated successfully" });
                setImageFile(null);
            } else {
                setMessage({ type: "info", content: "No changes to save" });
            }
        } catch (error) {
            console.error(error);
            setMessage({
                type: "error",
                content: error.message || "Failed to update profile"
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="max-w-4xl">
            <div className="mb-8">
                <h2 className="text-xl font-semibold text-gray-900">Profile Settings</h2>
                <p className="text-sm text-gray-500 mt-1">
                    Update your personal information and profile picture
                </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-8">
                {/* Profile Picture Section */}
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <h3 className="text-base font-medium text-gray-900 mb-4">Profile Picture</h3>
                    <div className="flex items-center gap-6">
                        <div className="relative group">
                            <div className="w-24 h-24 rounded-full overflow-hidden bg-emerald-100 flex items-center justify-center border-4 border-white shadow-md">
                                {imagePreview ? (
                                    <img
                                        src={imagePreview}
                                        alt="Profile"
                                        className="w-full h-full object-cover"
                                    />
                                ) : (
                                    <span className="text-2xl font-bold text-emerald-600">
                                        {formData.firstName?.[0]}
                                        {formData.lastName?.[0]}
                                    </span>
                                )}

                                <label className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition cursor-pointer">
                                    <Camera className="w-8 h-8 text-white" />
                                    <input
                                        type="file"
                                        className="hidden"
                                        accept="image/*"
                                        onChange={handleImageChange}
                                    />
                                </label>
                            </div>
                        </div>

                        <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900">Upload your photo</p>
                            <p className="text-sm text-gray-500 mt-1">
                                Photos help your students recognize you.
                            </p>
                            <div className="flex gap-3 mt-3">
                                <button
                                    type="button"
                                    className="text-sm font-medium text-emerald-600 hover:text-emerald-700"
                                    onClick={() => document.querySelector('input[type="file"]').click()}
                                >
                                    Change
                                </button>
                                {imagePreview && (
                                    <button
                                        type="button"
                                        className="text-sm font-medium text-red-600 hover:text-red-700"
                                        onClick={() => {
                                            setImagePreview(null);
                                            setImageFile(null);
                                            // Note: We don't delete from backend here yet, just UI preview reset or if user wants to remove current pic?
                                            // Backend doesn't have delete profile pic endpoint yet.
                                        }}
                                    >
                                        Remove
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Personal Information */}
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <h3 className="text-base font-medium text-gray-900 mb-6">Personal Information</h3>

                    <div className="grid grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                First Name
                            </label>
                            <input
                                type="text"
                                value={formData.firstName}
                                onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Last Name
                            </label>
                            <input
                                type="text"
                                value={formData.lastName}
                                onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
                            />
                        </div>

                        <div className="col-span-2">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Email Address
                            </label>
                            <input
                                type="email"
                                value={formData.email}
                                disabled
                                className="w-full px-4 py-2 border border-gray-200 bg-gray-50 rounded-lg text-gray-500"
                            />
                            <p className="text-xs text-gray-500 mt-1">
                                Email address cannot be changed. Please contact admin for support.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Messages */}
                {message.content && (
                    <div className={`p-4 rounded-lg flex items-center gap-2 ${message.type === 'success' ? 'bg-emerald-50 text-emerald-700' :
                        message.type === 'error' ? 'bg-red-50 text-red-700' : 'bg-blue-50 text-blue-700'
                        }`}>
                        {message.type === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                        {message.content}
                    </div>
                )}

                <div className="flex justify-end pt-4">
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="flex items-center gap-2 bg-emerald-600 text-white px-6 py-2.5 rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 transition disabled:opacity-70 disabled:cursor-not-allowed"
                    >
                        {isLoading ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                            <Save className="w-4 h-4" />
                        )}
                        Save Changes
                    </button>
                </div>
            </form>
        </div>
    );
};

export default ProfileSettings;

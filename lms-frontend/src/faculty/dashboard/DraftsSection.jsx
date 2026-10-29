import { useState, useEffect } from "react";
import { Video, FileText, Loader2, AlertCircle } from "lucide-react";
import facultyApi from "../../utils/facultyApi";
import ContentList from "./ContentList";
import ConfirmationModal from "../../components/common/ConfirmationModal";

const DraftsSection = () => {
    const [activeTab, setActiveTab] = useState("videos"); // videos | documents
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [publishTarget, setPublishTarget] = useState(null);

    const fetchDrafts = async () => {
        setLoading(true);
        setError("");
        try {
            let response;
            if (activeTab === "videos") {
                response = await facultyApi.getMyVideos({ status: 'processing', visibility: "private" }); // Assuming private = draft. Also checking processing just in case, but visibility is key.
                // Actually, let's stick to visibility 'private' as per plan
                response = await facultyApi.getMyVideos({ visibility: "private" });
            } else {
                response = await facultyApi.getMyDocuments({ visibility: "private" });
            }

            if (response.success) {
                setItems(response.data || []);
            }
        } catch (err) {
            console.error("Failed to fetch drafts:", err);
            setError("Failed to load drafts");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDrafts();
    }, [activeTab]);

    const handlePublish = (item) => {
        setPublishTarget(item);
    };

    const handleConfirmPublish = async () => {
        if (!publishTarget) return;
        try {
            if (activeTab === "videos") {
                await facultyApi.updateVideoVisibility(publishTarget.id, "public");
            } else {
                await facultyApi.updateDocument(publishTarget.id, { visibility: "public" });
            }
            // Refresh list
            fetchDrafts();
        } catch (err) {
            console.error("Failed to publish:", err);
            alert("Failed to publish content");
        } finally {
            setPublishTarget(null);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Drafts</h2>
                    <p className="text-gray-500 mt-1">
                        Manage your unpublished content
                    </p>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-4 border-b border-gray-200">
                <button
                    onClick={() => setActiveTab("videos")}
                    className={`pb-4 px-2 font-medium flex items-center gap-2 transition-colors relative ${activeTab === "videos"
                            ? "text-emerald-600"
                            : "text-gray-500 hover:text-gray-700"
                        }`}
                >
                    <Video className="w-5 h-5" />
                    Videos
                    {activeTab === "videos" && (
                        <div className="absolute bottom-0 left-0 w-full h-0.5 bg-emerald-600 rounded-t-full" />
                    )}
                </button>
                <button
                    onClick={() => setActiveTab("documents")}
                    className={`pb-4 px-2 font-medium flex items-center gap-2 transition-colors relative ${activeTab === "documents"
                            ? "text-emerald-600"
                            : "text-gray-500 hover:text-gray-700"
                        }`}
                >
                    <FileText className="w-5 h-5" />
                    Documents
                    {activeTab === "documents" && (
                        <div className="absolute bottom-0 left-0 w-full h-0.5 bg-emerald-600 rounded-t-full" />
                    )}
                </button>
            </div>

            {/* Content */}
            {loading ? (
                <div className="flex justify-center py-12">
                    <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
                </div>
            ) : error ? (
                <div className="flex flex-col items-center justify-center py-12 text-red-500">
                    <AlertCircle className="w-8 h-8 mb-2" />
                    <p>{error}</p>
                </div>
            ) : (
                <ContentList
                    items={items}
                    type={activeTab === "videos" ? "video" : "document"}
                    onActionClick={handlePublish}
                    actionLabel="Publish"
                />
            )}

            <ConfirmationModal
                isOpen={!!publishTarget}
                onClose={() => setPublishTarget(null)}
                onConfirm={handleConfirmPublish}
                title="Publish Content"
                message={`Are you sure you want to publish "${publishTarget?.title}"?`}
                confirmText="Publish"
                cancelText="Cancel"
                isDanger={false}
            />
        </div>
    );
};

export default DraftsSection;

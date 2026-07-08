import { useState, useEffect } from "react";
import { Video, FileText, Loader2, AlertCircle } from "lucide-react";
import facultyApi from "../../utils/facultyApi";
import ContentList from "./ContentList";

const PublishedSection = () => {
    const [activeTab, setActiveTab] = useState("videos"); // videos | documents
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const fetchPublished = async () => {
        setLoading(true);
        setError("");
        try {
            let response;
            if (activeTab === "videos") {
                response = await facultyApi.getMyVideos({ visibility: "public" });
            } else {
                response = await facultyApi.getMyDocuments({ visibility: "public" });
            }

            if (response.success) {
                setItems(response.data || []);
            }
        } catch (err) {
            console.error("Failed to fetch published content:", err);
            setError("Failed to load published content");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPublished();
    }, [activeTab]);

    const handleUnpublish = async (item) => {
        if (!window.confirm(`Are you sure you want to unpublish "${item.title}"?`)) return;

        try {
            if (activeTab === "videos") {
                await facultyApi.updateVideoVisibility(item.id, "private");
            } else {
                await facultyApi.updateDocument(item.id, { visibility: "private" });
            }
            // Refresh list
            fetchPublished();
        } catch (err) {
            console.error("Failed to unpublish:", err);
            alert("Failed to unpublish content");
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Published Content</h2>
                    <p className="text-gray-500 mt-1">
                        Manage your live content
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
                    onActionClick={handleUnpublish}
                    actionLabel="Unpublish"
                />
            )}
        </div>
    );
};

export default PublishedSection;

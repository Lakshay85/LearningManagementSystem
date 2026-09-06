import { Video, FileText, Clock, Eye, Download, Play } from "lucide-react";

// Format relative time
const formatRelativeTime = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    if (diffInSeconds < 60) return "Just now";
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} min ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`;
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
};

// Format duration
const formatDuration = (seconds) => {
    if (!seconds) return "N/A";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
};

// Format file size
const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

const ContentList = ({ items, type, onActionClick, actionLabel = "View" }) => {
    if (!items || items.length === 0) {
        return (
            <div className="p-8 text-center bg-white rounded-xl border border-gray-200 shadow-sm">
                {type === "video" ? (
                    <Video className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                ) : (
                    <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                )}
                <p className="text-gray-500">No {type}s found in this section</p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="divide-y divide-gray-200">
                {items.map((item) => (
                    <div
                        key={item.id}
                        className="p-4 flex items-center gap-4 hover:bg-gray-50 transition-colors"
                    >
                        {/* Thumbnail / Icon */}
                        <div className={`w-32 h-20 ${type === 'video' ? 'bg-gray-200' : 'bg-emerald-50'} rounded-lg flex items-center justify-center flex-shrink-0`}>
                            {type === "video" ? (
                                item.thumbnailPath ? (
                                    <img
                                        src={item.thumbnailPath}
                                        alt={item.title}
                                        className="w-full h-full object-cover rounded-lg"
                                    />
                                ) : (
                                    <Play className="w-8 h-8 text-gray-400" />
                                )
                            ) : (
                                <FileText className="w-8 h-8 text-emerald-500" />
                            )}
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                            <h4 className="font-medium text-gray-900 truncate">
                                {item.title}
                            </h4>
                            <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                                {type === "video" && (
                                    <>
                                        <span className="flex items-center gap-1">
                                            <Eye className="w-4 h-4" />
                                            {(item.viewCount || 0).toLocaleString()} views
                                        </span>
                                        <span className="flex items-center gap-1">
                                            <Clock className="w-4 h-4" />
                                            {formatDuration(item.duration)}
                                        </span>
                                    </>
                                )}
                                {type === "document" && (
                                    <span className="flex items-center gap-1">
                                        <Download className="w-4 h-4" />
                                        {formatFileSize(item.fileSize)}
                                    </span>
                                )}
                                <span className="text-xs text-gray-400">• {formatRelativeTime(item.createdAt)}</span>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => onActionClick(item)}
                                className="px-3 py-1.5 text-sm text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors font-medium"
                            >
                                {actionLabel}
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ContentList;

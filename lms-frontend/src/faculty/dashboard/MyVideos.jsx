import { useState, useEffect, useCallback } from "react";
import {
  Video,
  Play,
  Edit2,
  Trash2,
  Eye,
  EyeOff,
  Clock,
  Calendar,
  MoreVertical,
  Search,
  Filter,
  Loader2,
  AlertCircle,
  RefreshCw,
  FileVideo,
  Globe,
  Lock,
  Link as LinkIcon,
} from "lucide-react";
import VideoPlayerModal from "./VideoPlayerModal";
import facultyApi from "../../utils/facultyApi";
import CustomSelect from "../../components/common/CustomSelect";

// Format file size
const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

// Format date
const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
};

// Format relative time
const formatRelativeTime = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);

  if (diffInSeconds < 60) return "Just now";
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} min ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`;
  return formatDate(dateString);
};

// Visibility icon component
const VisibilityIcon = ({ visibility }) => {
  switch (visibility) {
    case "public":
      return <Globe className="w-4 h-4 text-green-600" />;
    case "private":
      return <Lock className="w-4 h-4 text-red-500" />;
    case "unlisted":
      return <LinkIcon className="w-4 h-4 text-yellow-600" />;
    default:
      return <Eye className="w-4 h-4 text-gray-500" />;
  }
};

// Status badge component
const StatusBadge = ({ status }) => {
  const statusConfig = {
    ready: { bg: "bg-green-100", text: "text-green-700", label: "Ready" },
    processing: { bg: "bg-yellow-100", text: "text-yellow-700", label: "Processing" },
    failed: { bg: "bg-red-100", text: "text-red-700", label: "Failed" },
    deleted: { bg: "bg-gray-100", text: "text-gray-700", label: "Deleted" },
  };

  const config = statusConfig[status] || statusConfig.ready;

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  );
};

// Category badge component
const CategoryBadge = ({ category }) => {
  const categoryConfig = {
    lecture: { bg: "bg-blue-100", text: "text-blue-700" },
    tutorial: { bg: "bg-purple-100", text: "text-purple-700" },
    lab: { bg: "bg-orange-100", text: "text-orange-700" },
    seminar: { bg: "bg-indigo-100", text: "text-indigo-700" },
    workshop: { bg: "bg-pink-100", text: "text-pink-700" },
    other: { bg: "bg-gray-100", text: "text-gray-700" },
  };

  const config = categoryConfig[category] || categoryConfig.other;

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${config.bg} ${config.text}`}>
      {category}
    </span>
  );
};

// Video card component
const VideoCard = ({ video, onEdit, onDelete, onView }) => {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow duration-300 group">
      {/* Thumbnail / Video Preview */}
      <div className="relative aspect-video bg-gray-900">
        {/* Placeholder thumbnail with play button */}
        <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-gray-800 to-gray-900">
          <FileVideo className="w-16 h-16 text-gray-600" />
        </div>

        {/* Play overlay on hover */}
        <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
          onClick={() => onView(video)}>
          <div className="w-14 h-14 rounded-full bg-white/90 flex items-center justify-center">
            <Play className="w-6 h-6 text-gray-900 ml-1" />
          </div>
        </div>

        {/* Duration badge */}
        {video.duration && (
          <div className="absolute bottom-2 right-2 px-2 py-1 bg-black/80 text-white text-xs rounded">
            {video.duration}
          </div>
        )}

        {/* Status badge */}
        <div className="absolute top-2 left-2">
          <StatusBadge status={video.status} />
        </div>

        {/* Visibility indicator */}
        <div className="absolute top-2 right-2 p-1.5 bg-white/90 rounded-full">
          <VisibilityIcon visibility={video.visibility} />
        </div>
      </div>

      {/* Video Info */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-gray-900 line-clamp-2 flex-1" title={video.title}>
            {video.title}
          </h3>

          {/* More options menu */}
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="p-1 hover:bg-gray-100 rounded-full transition-colors"
            >
              <MoreVertical className="w-5 h-5 text-gray-500" />
            </button>

            {showMenu && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)} />
                <div className="absolute right-0 top-8 z-20 bg-white rounded-lg shadow-lg border border-gray-200 py-1 min-w-[140px]">
                  <button
                    onClick={() => { onView(video); setShowMenu(false); }}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                  >
                    <Play className="w-4 h-4" /> Play
                  </button>
                  <button
                    onClick={() => { onEdit(video); setShowMenu(false); }}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                  >
                    <Edit2 className="w-4 h-4" /> Edit
                  </button>
                  <button
                    onClick={() => { onDelete(video); setShowMenu(false); }}
                    className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" /> Delete
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Description */}
        {video.description && (
          <p className="text-sm text-gray-500 mt-2 line-clamp-2">
            {video.description}
          </p>
        )}

        {/* Meta info */}
        <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5" />
            <span>{formatRelativeTime(video.createdAt)}</span>
          </div>
          <div className="flex items-center gap-1">
            <Eye className="w-3.5 h-3.5" />
            <span>{video.viewCount || 0} views</span>
          </div>
        </div>

        {/* Tags */}
        <div className="flex items-center gap-2 mt-3">
          <CategoryBadge category={video.category} />
          <span className="text-xs text-gray-400">{formatFileSize(video.fileSize)}</span>
        </div>
      </div>
    </div>
  );
};

const MyVideos = ({ setActiveTab }) => {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [visibilityFilter, setVisibilityFilter] = useState("");
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 12,
    total: 0,
    totalPages: 0,
  });
  const [selectedVideo, setSelectedVideo] = useState(null);

  // Fetch videos
  const fetchVideos = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const params = {
        page: pagination.page,
        limit: pagination.limit,
      };

      if (searchQuery) params.search = searchQuery;
      if (categoryFilter) params.category = categoryFilter;
      if (visibilityFilter) params.visibility = visibilityFilter;

      const data = await facultyApi.getMyVideos(params);

      if (data.success) {
        setVideos(data.data || []);
        setPagination((prev) => ({
          ...prev,
          total: data.total || 0,
          totalPages: data.totalPages || 0,
        }));
      }
    } catch (err) {
      if (err.status === 401) {
        setError("Please login to view your videos");
      } else {
        setError(err.message || "Failed to load videos");
      }
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.limit, searchQuery, categoryFilter, visibilityFilter]);

  useEffect(() => {
    fetchVideos();
  }, [fetchVideos]);

  // Handle search
  const handleSearch = (e) => {
    e.preventDefault();
    setPagination((prev) => ({ ...prev, page: 1 }));
    fetchVideos();
  };

  // Handle view video
  const handleView = (video) => {
    setSelectedVideo(video);
  };

  // Handle edit video
  const handleEdit = (video) => {
    // TODO: Implement edit modal/page
    console.log("Edit video:", video);
    alert("Edit functionality coming soon!");
  };

  // Handle delete video
  const handleDelete = async (video) => {
    if (!confirm(`Are you sure you want to delete "${video.title}"?`)) {
      return;
    }

    try {
      await facultyApi.deleteVideo(video.id);
      // Remove from list
      setVideos((prev) => prev.filter((v) => v.id !== video.id));
    } catch (err) {
      alert(err.message || "Failed to delete video");
    }
  };

  // Handle page change
  const handlePageChange = (newPage) => {
    setPagination((prev) => ({ ...prev, page: newPage }));
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">My Videos</h2>
          <p className="text-gray-500 mt-1">
            Manage your uploaded educational content
          </p>
        </div>
        <button
          onClick={() => setActiveTab("upload")}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
        >
          <Video className="w-5 h-5" />
          Upload New Video
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <form onSubmit={handleSearch} className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search videos..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>
          </form>

          {/* Category Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-400 shrink-0" />
            <div className="min-w-[150px]">
              <CustomSelect
                value={categoryFilter}
                onChange={(e) => {
                  setCategoryFilter(e.target.value);
                  setPagination((prev) => ({ ...prev, page: 1 }));
                }}
                className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm"
                options={[
                  { value: "", label: "All Categories" },
                  { value: "lecture", label: "Lecture" },
                  { value: "tutorial", label: "Tutorial" },
                  { value: "lab", label: "Lab" },
                  { value: "seminar", label: "Seminar" },
                  { value: "workshop", label: "Workshop" },
                  { value: "other", label: "Other" },
                ]}
              />
            </div>
          </div>

          {/* Visibility Filter */}
          <div className="min-w-[140px]">
            <CustomSelect
              value={visibilityFilter}
              onChange={(e) => {
                setVisibilityFilter(e.target.value);
                setPagination((prev) => ({ ...prev, page: 1 }));
              }}
              className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm"
              options={[
                { value: "", label: "All Visibility" },
                { value: "public", label: "Public" },
                { value: "private", label: "Private" },
                { value: "unlisted", label: "Unlisted" },
              ]}
            />
          </div>

          {/* Refresh Button */}
          <button
            onClick={fetchVideos}
            disabled={loading}
            className="p-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 text-gray-600 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
          <span className="ml-3 text-gray-600">Loading videos...</span>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="flex flex-col items-center justify-center py-12">
          <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
          <p className="text-gray-900 font-medium">{error}</p>
          <button
            onClick={fetchVideos}
            className="mt-4 px-4 py-2 text-emerald-600 hover:text-emerald-700"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && videos.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 bg-white rounded-xl border border-gray-200">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <Video className="w-10 h-10 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No videos yet</h3>
          <p className="text-gray-500 mb-6 text-center max-w-md">
            Start sharing your educational content by uploading your first video.
          </p>
          <button
            onClick={() => setActiveTab("upload")}
            className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
          >
            <Video className="w-5 h-5" />
            Upload Your First Video
          </button>
        </div>
      )}

      {/* Video Grid */}
      {!loading && !error && videos.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {videos.map((video) => (
              <VideoCard
                key={video.id}
                video={video}
                onView={handleView}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            ))}
          </div>

          {/* Pagination */}
          {pagination.totalPages > 1 && (
            <div className="flex items-center justify-between mt-8 bg-white rounded-xl border border-gray-200 px-4 py-3">
              <p className="text-sm text-gray-600">
                Showing {(pagination.page - 1) * pagination.limit + 1} to{" "}
                {Math.min(pagination.page * pagination.limit, pagination.total)} of{" "}
                {pagination.total} videos
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={pagination.page === 1}
                  className="px-3 py-1 border border-gray-200 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                {Array.from({ length: Math.min(5, pagination.totalPages) }, (_, i) => {
                  let pageNum;
                  if (pagination.totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (pagination.page <= 3) {
                    pageNum = i + 1;
                  } else if (pagination.page >= pagination.totalPages - 2) {
                    pageNum = pagination.totalPages - 4 + i;
                  } else {
                    pageNum = pagination.page - 2 + i;
                  }
                  return (
                    <button
                      key={pageNum}
                      onClick={() => handlePageChange(pageNum)}
                      className={`w-8 h-8 rounded-lg text-sm ${pagination.page === pageNum
                          ? "bg-emerald-600 text-white"
                          : "border border-gray-200 hover:bg-gray-50"
                        }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
                <button
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={pagination.page === pagination.totalPages}
                  className="px-3 py-1 border border-gray-200 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
      {/* Video Player Modal */}
      {selectedVideo && (
        <VideoPlayerModal
          videoUrl={facultyApi.getVideoStreamUrl(selectedVideo.id)}
          title={selectedVideo.title}
          onClose={() => setSelectedVideo(null)}
        />
      )}
    </div>
  );
};

export default MyVideos;

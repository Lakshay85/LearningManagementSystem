import { useState, useEffect, useCallback } from "react";
import {
  Video,
  FileText,
  File,
  Play,
  Download,
  Edit2,
  Trash2,
  Clock,
  Calendar,
  MoreVertical,
  Search,
  Filter,
  Loader2,
  AlertCircle,
  RefreshCw,
  FileVideo,
  Image as ImageIcon,
  FileArchive,
  FileSpreadsheet,
  X,
  SlidersHorizontal,
} from "lucide-react";
import VideoPlayerModal from "./VideoPlayerModal";
import facultyApi from "../../utils/facultyApi";

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
  if (diffInSeconds < 86400)
    return `${Math.floor(diffInSeconds / 3600)} hours ago`;
  if (diffInSeconds < 604800)
    return `${Math.floor(diffInSeconds / 86400)} days ago`;
  return formatDate(dateString);
};

// Get file icon based on type
const getFileIcon = (fileType, mimeType) => {
  if (fileType === "video" || mimeType?.startsWith("video/")) {
    return <FileVideo className="w-8 h-8 text-blue-600" />;
  }
  if (mimeType?.includes("pdf")) {
    return <FileText className="w-8 h-8 text-red-600" />;
  }
  if (mimeType?.includes("word") || mimeType?.includes("document")) {
    return <FileText className="w-8 h-8 text-blue-700" />;
  }
  if (mimeType?.includes("sheet") || mimeType?.includes("excel")) {
    return <FileSpreadsheet className="w-8 h-8 text-green-600" />;
  }
  if (mimeType?.includes("presentation") || mimeType?.includes("powerpoint")) {
    return <FileText className="w-8 h-8 text-orange-600" />;
  }
  if (mimeType?.startsWith("image/")) {
    return <ImageIcon className="w-8 h-8 text-purple-600" />;
  }
  if (
    mimeType?.includes("zip") ||
    mimeType?.includes("rar") ||
    mimeType?.includes("archive")
  ) {
    return <FileArchive className="w-8 h-8 text-yellow-600" />;
  }
  return <File className="w-8 h-8 text-gray-600" />;
};

// Get file type label
const getFileTypeLabel = (fileType, mimeType) => {
  if (fileType === "video") return "Video";
  if (mimeType?.includes("pdf")) return "PDF";
  if (mimeType?.includes("word")) return "Word Document";
  if (mimeType?.includes("sheet") || mimeType?.includes("excel"))
    return "Spreadsheet";
  if (mimeType?.includes("presentation")) return "Presentation";
  if (mimeType?.includes("image")) return "Image";
  if (mimeType?.includes("zip") || mimeType?.includes("archive"))
    return "Archive";
  return "Document";
};

// Content card component
const ContentCard = ({ content, onView, onEdit, onDelete, onDownload }) => {
  const [showMenu, setShowMenu] = useState(false);
  const isVideo = content.type === "video";

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow duration-300 group">
      {/* Thumbnail / Preview */}
      <div className="relative aspect-video bg-gradient-to-br from-gray-100 to-gray-200">
        <div className="absolute inset-0 flex items-center justify-center">
          {getFileIcon(content.type, content.mimeType)}
        </div>

        {/* Hover overlay */}
        <div
          className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
          onClick={() => onView(content)}
        >
          <div className="w-14 h-14 rounded-full bg-white/90 flex items-center justify-center">
            {isVideo ? (
              <Play className="w-6 h-6 text-gray-900 ml-1" />
            ) : (
              <Download className="w-6 h-6 text-gray-900" />
            )}
          </div>
        </div>

        {/* Duration badge for videos */}
        {isVideo && content.duration && (
          <div className="absolute bottom-2 right-2 px-2 py-1 bg-black/80 text-white text-xs rounded">
            {content.duration}
          </div>
        )}

        {/* File type badge */}
        <div className="absolute top-2 left-2">
          <span className="px-2 py-1 bg-white/90 backdrop-blur-sm text-gray-700 text-xs font-medium rounded-full">
            {getFileTypeLabel(content.type, content.mimeType)}
          </span>
        </div>

        {/* File size */}
        <div className="absolute bottom-2 left-2 px-2 py-1 bg-black/80 text-white text-xs rounded">
          {formatFileSize(content.fileSize)}
        </div>
      </div>

      {/* Content Info */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <h3
            className="font-semibold text-gray-900 line-clamp-2 flex-1"
            title={content.title}
          >
            {content.title}
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
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowMenu(false)}
                />
                <div className="absolute right-0 top-8 z-20 bg-white rounded-lg shadow-lg border border-gray-200 py-1 min-w-[140px]">
                  <button
                    onClick={() => {
                      onView(content);
                      setShowMenu(false);
                    }}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                  >
                    {isVideo ? (
                      <Play className="w-4 h-4" />
                    ) : (
                      <Download className="w-4 h-4" />
                    )}
                    {isVideo ? "Play" : "Download"}
                  </button>
                  <button
                    onClick={() => {
                      onEdit(content);
                      setShowMenu(false);
                    }}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                  >
                    <Edit2 className="w-4 h-4" /> Edit
                  </button>
                  <button
                    onClick={() => {
                      onDelete(content);
                      setShowMenu(false);
                    }}
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
        {content.description && (
          <p className="text-sm text-gray-500 mt-2 line-clamp-2">
            {content.description}
          </p>
        )}

        {/* Meta info */}
        <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5" />
            <span>{formatRelativeTime(content.createdAt)}</span>
          </div>
          {content.viewCount !== undefined && (
            <div className="flex items-center gap-1">
              <Play className="w-3.5 h-3.5" />
              <span>{content.viewCount} views</span>
            </div>
          )}
        </div>

        {/* Category/Course info if available */}
        {content.category && (
          <div className="mt-3">
            <span className="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs font-medium rounded-full capitalize">
              {content.category}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

const AllContent = ({ setActiveTab }) => {
  const [contents, setContents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  // Filter states
  const [fileTypeFilter, setFileTypeFilter] = useState("");
  const [timeFilter, setTimeFilter] = useState("");
  const [sizeFilter, setSizeFilter] = useState("");
  const [sortBy, setSortBy] = useState("newest");

  const [pagination, setPagination] = useState({
    page: 1,
    limit: 12,
    total: 0,
    totalPages: 0,
  });
  const [selectedVideo, setSelectedVideo] = useState(null);

  // Fetch all content (videos + documents)
  const fetchContent = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const params = {
        page: pagination.page,
        limit: pagination.limit,
      };

      if (searchQuery) params.search = searchQuery;
      if (fileTypeFilter) params.fileType = fileTypeFilter;
      if (timeFilter) params.timeRange = timeFilter;
      if (sizeFilter) params.sizeRange = sizeFilter;
      if (sortBy) params.sortBy = sortBy;

      const data = await facultyApi.getAllContent(params);

      if (data.success) {
        setContents(data.data || []);
        setPagination((prev) => ({
          ...prev,
          total: data.total || 0,
          totalPages: data.totalPages || 0,
        }));
      }
    } catch (err) {
      if (err.status === 401) {
        setError("Please login to view your content");
      } else {
        setError(err.message || "Failed to load content");
      }
    } finally {
      setLoading(false);
    }
  }, [
    pagination.page,
    pagination.limit,
    searchQuery,
    fileTypeFilter,
    timeFilter,
    sizeFilter,
    sortBy,
  ]);

  useEffect(() => {
    fetchContent();
  }, [fetchContent]);

  // Handle search
  const handleSearch = (e) => {
    e.preventDefault();
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  // Handle view content
  const handleView = (content) => {
    if (content.type === "video") {
      setSelectedVideo(content);
    } else if (content.documentId) {
      window.open(
        facultyApi.getDocumentDownloadUrl(content.documentId),
        "_blank"
      );
    }
  };

  // Handle edit content
  const handleEdit = (content) => {
    console.log("Edit content:", content);
    alert("Edit functionality coming soon!");
  };

  // Handle delete content
  const handleDelete = async (content) => {
    if (!confirm(`Are you sure you want to delete "${content.title}"?`)) {
      return;
    }

    try {
      if (content.type === "video") {
        await facultyApi.deleteVideo(content.id);
      } else {
        await facultyApi.deleteContent(content.id);
      }
      setContents((prev) => prev.filter((c) => c.id !== content.id));
    } catch (err) {
      alert(err.message || "Failed to delete content");
    }
  };

  // Handle download
  const handleDownload = (content) => {
    if (content.type !== "video" && content.documentId) {
      window.open(
        facultyApi.getDocumentDownloadUrl(content.documentId),
        "_blank"
      );
    }
  };

  // Handle page change
  const handlePageChange = (newPage) => {
    setPagination((prev) => ({ ...prev, page: newPage }));
  };

  // Clear all filters
  const clearFilters = () => {
    setFileTypeFilter("");
    setTimeFilter("");
    setSizeFilter("");
    setSortBy("newest");
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const activeFiltersCount = [fileTypeFilter, timeFilter, sizeFilter].filter(
    Boolean
  ).length;

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">All Content</h2>
          <p className="text-gray-500 mt-1">
            Manage all your uploaded videos and documents
          </p>
        </div>
        <button
          onClick={() => setActiveTab("upload")}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
        >
          <Video className="w-5 h-5" />
          Upload Content
        </button>
      </div>

      {/* Search and Filters Bar */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <form onSubmit={handleSearch} className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search content by title, description..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>
          </form>

          {/* Filter Toggle Button */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-4 py-2 border rounded-lg transition-colors ${showFilters || activeFiltersCount > 0
              ? "border-emerald-600 bg-emerald-50 text-emerald-700"
              : "border-gray-200 hover:bg-gray-50"
              }`}
          >
            <SlidersHorizontal className="w-5 h-5" />
            <span>Filters</span>
            {activeFiltersCount > 0 && (
              <span className="px-2 py-0.5 bg-emerald-600 text-white text-xs rounded-full">
                {activeFiltersCount}
              </span>
            )}
          </button>

          {/* Refresh Button */}
          <button
            onClick={fetchContent}
            disabled={loading}
            className="p-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw
              className={`w-5 h-5 text-gray-600 ${loading ? "animate-spin" : ""
                }`}
            />
          </button>
        </div>

        {/* Expandable Filters */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* File Type Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  File Type
                </label>
                <select
                  value={fileTypeFilter}
                  onChange={(e) => {
                    setFileTypeFilter(e.target.value);
                    setPagination((prev) => ({ ...prev, page: 1 }));
                  }}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="">All Types</option>
                  <option value="video">Videos</option>
                  <option value="pdf">PDF Documents</option>
                  <option value="word">Word Documents</option>
                  <option value="excel">Spreadsheets</option>
                  <option value="powerpoint">Presentations</option>
                  <option value="image">Images</option>
                  <option value="other">Other</option>
                </select>
              </div>

              {/* Time Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload Time
                </label>
                <select
                  value={timeFilter}
                  onChange={(e) => {
                    setTimeFilter(e.target.value);
                    setPagination((prev) => ({ ...prev, page: 1 }));
                  }}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="">All Time</option>
                  <option value="today">Today</option>
                  <option value="week">This Week</option>
                  <option value="month">This Month</option>
                  <option value="quarter">Last 3 Months</option>
                  <option value="year">This Year</option>
                </select>
              </div>

              {/* Size Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  File Size
                </label>
                <select
                  value={sizeFilter}
                  onChange={(e) => {
                    setSizeFilter(e.target.value);
                    setPagination((prev) => ({ ...prev, page: 1 }));
                  }}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="">All Sizes</option>
                  <option value="small">Small (&lt; 10 MB)</option>
                  <option value="medium">Medium (10-100 MB)</option>
                  <option value="large">Large (100-500 MB)</option>
                  <option value="xlarge">Very Large (&gt; 500 MB)</option>
                </select>
              </div>

              {/* Sort By */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sort By
                </label>
                <select
                  value={sortBy}
                  onChange={(e) => {
                    setSortBy(e.target.value);
                    setPagination((prev) => ({ ...prev, page: 1 }));
                  }}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="newest">Newest First</option>
                  <option value="oldest">Oldest First</option>
                  <option value="title">Title (A-Z)</option>
                  <option value="size-desc">Largest First</option>
                  <option value="size-asc">Smallest First</option>
                  <option value="popular">Most Popular</option>
                </select>
              </div>
            </div>

            {/* Clear Filters */}
            {activeFiltersCount > 0 && (
              <div className="mt-4 flex justify-end">
                <button
                  onClick={clearFilters}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-4 h-4" />
                  Clear All Filters
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Stats Summary */}
      {!loading && !error && contents.length > 0 && (
        <div className="bg-gradient-to-r from-emerald-50 to-blue-50 rounded-xl border border-emerald-200 p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div>
                <p className="text-sm text-gray-600">Total Content</p>
                <p className="text-2xl font-bold text-gray-900">
                  {pagination.total}
                </p>
              </div>
              <div className="h-12 w-px bg-gray-300" />
              <div>
                <p className="text-sm text-gray-600">Showing</p>
                <p className="text-lg font-semibold text-gray-900">
                  {contents.length} item{contents.length !== 1 ? "s" : ""}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
          <span className="ml-3 text-gray-600">Loading content...</span>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="flex flex-col items-center justify-center py-12">
          <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
          <p className="text-gray-900 font-medium">{error}</p>
          <button
            onClick={fetchContent}
            className="mt-4 px-4 py-2 text-emerald-600 hover:text-emerald-700"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && contents.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 bg-white rounded-xl border border-gray-200">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <FileText className="w-10 h-10 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No content yet
          </h3>
          <p className="text-gray-500 mb-6 text-center max-w-md">
            {searchQuery || activeFiltersCount > 0
              ? "No content matches your search criteria. Try adjusting your filters."
              : "Start sharing your educational content by uploading videos or documents."}
          </p>
          {!searchQuery && activeFiltersCount === 0 && (
            <button
              onClick={() => setActiveTab("upload")}
              className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
            >
              <Video className="w-5 h-5" />
              Upload Your First Content
            </button>
          )}
        </div>
      )}

      {/* Content Grid */}
      {!loading && !error && contents.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {contents.map((content) => (
              <ContentCard
                key={content.id}
                content={content}
                onView={handleView}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onDownload={handleDownload}
              />
            ))}
          </div>

          {/* Pagination */}
          {pagination.totalPages > 1 && (
            <div className="flex items-center justify-between mt-8 bg-white rounded-xl border border-gray-200 px-4 py-3">
              <p className="text-sm text-gray-600">
                Showing {(pagination.page - 1) * pagination.limit + 1} to{" "}
                {Math.min(pagination.page * pagination.limit, pagination.total)}{" "}
                of {pagination.total} items
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={pagination.page === 1}
                  className="px-3 py-1 border border-gray-200 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                {Array.from(
                  { length: Math.min(5, pagination.totalPages) },
                  (_, i) => {
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
                  }
                )}
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

export default AllContent;

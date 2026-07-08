import { useState, useEffect } from "react";
import { Video, Users, Eye, Clock, Upload, TrendingUp, Play, Loader2, AlertCircle } from "lucide-react";
import VideoPlayerModal from "./VideoPlayerModal";
import facultyApi from "../../utils/facultyApi";

// Format relative time
const formatRelativeTime = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);

  if (diffInSeconds < 60) return "Just now";
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} min ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`;
  if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 604800)} weeks ago`;
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
};

// Format duration from seconds to MM:SS or HH:MM:SS
const formatDuration = (seconds) => {
  if (!seconds) return "N/A";
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  }
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

// Format large numbers
const formatNumber = (num) => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
};

const DashboardOverview = ({ setActiveTab }) => {
  const [stats, setStats] = useState(null);
  const [recentVideos, setRecentVideos] = useState([]);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      setError("");

      try {
        // Fetch both stats and recent videos in parallel
        const [statsResponse, videosResponse] = await Promise.all([
          facultyApi.getMyVideoStats(),
          facultyApi.getMyRecentVideos(5),
        ]);

        if (statsResponse.success) {
          setStats(statsResponse.data);
        }

        if (videosResponse.success) {
          setRecentVideos(videosResponse.data || []);
        }
      } catch (err) {
        console.error("Dashboard fetch error:", err);
        setError(err.message || "Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // Build stats array from fetched data
  const statsData = [
    {
      label: "Total Videos",
      value: stats ? stats.totalVideos.toString() : "0",
      change: stats ? `+${stats.videosThisMonth} this month` : "",
      icon: Video,
      color: "bg-blue-500",
    },
    {
      label: "Total Views",
      value: stats ? formatNumber(stats.totalViews) : "0",
      change: stats && stats.viewsGrowth !== 0 ? `${stats.viewsGrowth > 0 ? '+' : ''}${stats.viewsGrowth}% from last month` : "No change",
      icon: Eye,
      color: "bg-emerald-500",
    },
    {
      label: "Active Students",
      value: "—",
      change: "Coming soon",
      icon: Users,
      color: "bg-purple-500",
    },
    {
      label: "Watch Time",
      value: "—",
      change: "Coming soon",
      icon: Clock,
      color: "bg-orange-500",
    },
  ];

  // Handle view video
  const handleViewVideo = (video) => {
    setSelectedVideo(video);
  };

  // Handle edit video (placeholder)
  const handleEditVideo = (video) => {
    console.log("Edit video:", video);
    alert("Edit functionality coming soon!");
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
        <span className="ml-3 text-gray-600">Loading dashboard...</span>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
        <p className="text-gray-900 font-medium">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 text-emerald-600 hover:text-emerald-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Welcome Back!</h2>
          <p className="text-gray-500 mt-1">
            Here's what's happening with your content
          </p>
        </div>
        <button
          onClick={() => setActiveTab("upload")}
          className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors"
        >
          <Upload className="w-5 h-5" />
          Upload New Video
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statsData.map((stat) => (
          <div
            key={stat.label}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
          >
            <div className="flex items-center justify-between mb-4">
              <div
                className={`w-12 h-12 ${stat.color} rounded-lg flex items-center justify-center`}
              >
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              <TrendingUp className="w-5 h-5 text-emerald-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
            <p className="text-sm text-gray-500 mt-1">{stat.label}</p>
            <p className="text-xs text-emerald-600 mt-2">{stat.change}</p>
          </div>
        ))}
      </div>

      {/* Recent Videos Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Recent Videos</h3>
          <button
            onClick={() => setActiveTab("videos")}
            className="text-sm text-emerald-600 hover:text-emerald-700 font-medium"
          >
            View All
          </button>
        </div>
        <div className="divide-y divide-gray-200">
          {recentVideos.length === 0 ? (
            <div className="p-8 text-center">
              <Video className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No videos uploaded yet</p>
              <button
                onClick={() => setActiveTab("upload")}
                className="mt-3 text-emerald-600 hover:text-emerald-700 font-medium text-sm"
              >
                Upload your first video
              </button>
            </div>
          ) : (
            recentVideos.map((video) => (
              <div
                key={video.id}
                className="p-4 flex items-center gap-4 hover:bg-gray-50 transition-colors"
              >
                {/* Video Thumbnail */}
                <div className="w-32 h-20 bg-gray-200 rounded-lg flex items-center justify-center flex-shrink-0">
                  {video.thumbnailPath ? (
                    <img
                      src={video.thumbnailPath}
                      alt={video.title}
                      className="w-full h-full object-cover rounded-lg"
                    />
                  ) : (
                    <Play className="w-8 h-8 text-gray-400" />
                  )}
                </div>

                {/* Video Info */}
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-gray-900 truncate">
                    {video.title}
                  </h4>
                  <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <Eye className="w-4 h-4" />
                      {(video.viewCount || 0).toLocaleString()} views
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {formatDuration(video.duration)}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">{formatRelativeTime(video.createdAt)}</p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleEditVideo(video)}
                    className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleViewVideo(video)}
                    className="px-3 py-1.5 text-sm text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors"
                  >
                    View
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <button
          onClick={() => setActiveTab("upload")}
          className="p-6 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl text-white text-left hover:from-emerald-600 hover:to-teal-700 transition-colors"
        >
          <Upload className="w-8 h-8 mb-3" />
          <h3 className="font-semibold text-lg">Upload Video</h3>
          <p className="text-emerald-100 text-sm mt-1">
            Share new educational content
          </p>
        </button>

        <button
          onClick={() => setActiveTab("courses")}
          className="p-6 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl text-white text-left hover:from-blue-600 hover:to-indigo-700 transition-colors"
        >
          <Video className="w-8 h-8 mb-3" />
          <h3 className="font-semibold text-lg">Manage Courses</h3>
          <p className="text-blue-100 text-sm mt-1">
            Organize your video content
          </p>
        </button>

        <button
          onClick={() => setActiveTab("analytics")}
          className="p-6 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl text-white text-left hover:from-purple-600 hover:to-pink-700 transition-colors"
        >
          <TrendingUp className="w-8 h-8 mb-3" />
          <h3 className="font-semibold text-lg">View Analytics</h3>
          <p className="text-purple-100 text-sm mt-1">
            Track your content performance
          </p>
        </button>
      </div>

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

export default DashboardOverview;

import { useState, useEffect, useRef } from "react";
import {
  Play,
  ChevronLeft,
  ChevronRight,
  Clock,
  Video,
  RefreshCw,
  MoreVertical,
  Heart,
  Share2
} from "lucide-react";

// Base URL handling - using what user prefers
const API_BASE_URL = "http://localhost:8000";

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
  if (diffInSeconds < 2592000)
    return `${Math.floor(diffInSeconds / 604800)} weeks ago`;
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

// Video Card Component matched to Dashboard Aesthetic
const VideoCard = ({ video, onPlay }) => {
  const uploaderName = video.uploader
    ? `${video.uploader.firstName || ""} ${video.uploader.lastName || ""}`.trim()
    : "Unknown Instructor";

  const uploaderInitials = video.uploader
    ? `${video.uploader.firstName?.[0] || ""}${video.uploader.lastName?.[0] || ""}`.toUpperCase()
    : "T";

  return (
    <div
      className="flex-shrink-0 w-80 bg-white rounded-3xl p-4 shadow-sm hover:shadow-md transition-all duration-300 border border-slate-100 group cursor-pointer snap-start"
      onClick={() => onPlay(video)}
    >
      {/* Thumbnail */}
      <div className="relative aspect-video rounded-2xl overflow-hidden mb-4 bg-slate-100">
        {video.thumbnailUrl ? (
          <img
            src={video.thumbnailUrl}
            alt={video.title}
            className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-slate-200 to-slate-300">
            <Video className="w-10 h-10 text-slate-400" />
          </div>
        )}

        {/* Hover Overlay */}
        <div className="absolute inset-0 bg-black/20 group-hover:bg-black/30 transition-colors duration-300 flex items-center justify-center">
          <div className="w-12 h-12 rounded-full bg-white/30 backdrop-blur-md flex items-center justify-center opacity-0 group-hover:opacity-100 transform translate-y-4 group-hover:translate-y-0 transition-all duration-300 shadow-lg">
            <Play className="w-6 h-6 text-white fill-current ml-1" />
          </div>
        </div>

        {/* Duration Badge */}
        {video.duration && (
          <span className="absolute bottom-3 right-3 px-2.5 py-1 bg-black/60 backdrop-blur-md rounded-lg text-xs font-medium text-white flex items-center gap-1.5">
            <Clock className="w-3 h-3" />
            {video.duration}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="space-y-3">
        <div className="flex justify-between items-start gap-2">
          <h3 className="font-bold text-slate-900 line-clamp-2 leading-tight group-hover:text-indigo-600 transition-colors">
            {video.title}
          </h3>
          <button className="text-slate-300 hover:text-slate-500 transition-colors">
            <MoreVertical className="w-5 h-5" />
          </button>
        </div>

        {/* Instructor Info */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600 text-xs font-bold ring-2 ring-white shadow-sm">
            {uploaderInitials}
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-bold text-slate-700 truncate max-w-[150px]">
              {uploaderName}
            </span>
            <span className="text-[10px] text-slate-500 font-medium">{video.viewCount || 0} views • {formatRelativeTime(video.createdAt)}</span>
          </div>
        </div>

        {/* Actions */}
        <div className="pt-3 border-t border-slate-50 flex items-center justify-between text-slate-400">
          <button className="flex items-center gap-1.5 text-xs font-medium hover:text-pink-500 transition-colors group/btn">
            <Heart className="w-4 h-4 group-hover/btn:fill-current" />
            Like
          </button>
          <button className="flex items-center gap-1.5 text-xs font-medium hover:text-indigo-600 transition-colors">
            <Share2 className="w-4 h-4" />
            Share
          </button>
        </div>
      </div>
    </div>
  );
};

const RecommendedVideos = () => {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const scrollContainerRef = useRef(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  // Fetch public videos
  const fetchVideos = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/videos/public?limit=20`, {
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error("Failed to fetch videos");
      }

      const data = await response.json();

      if (data.success) {
        setVideos(data.data || []);
      }
    } catch (err) {
      setError(err.message || "Failed to load videos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVideos();
  }, []);

  // Check scroll position
  const checkScrollPosition = () => {
    if (scrollContainerRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } =
        scrollContainerRef.current;
      setCanScrollLeft(scrollLeft > 0);
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 10);
    }
  };

  useEffect(() => {
    checkScrollPosition();
    const container = scrollContainerRef.current;
    if (container) {
      container.addEventListener("scroll", checkScrollPosition);
      window.addEventListener("resize", checkScrollPosition);
      return () => {
        container.removeEventListener("scroll", checkScrollPosition);
        window.removeEventListener("resize", checkScrollPosition);
      };
    }
  }, [videos]);

  // Scroll handlers
  const scroll = (direction) => {
    if (scrollContainerRef.current) {
      const scrollAmount = 340; // Approx card width + gap
      scrollContainerRef.current.scrollBy({
        left: direction === "left" ? -scrollAmount : scrollAmount,
        behavior: "smooth",
      });
    }
  };

  // Play video
  const handlePlay = (video) => {
    window.open(`${API_BASE_URL}/videos/stream/${video.id}`, "_blank");
  };

  // Loading state
  if (loading) {
    return (
      <div className="w-full bg-white rounded-[2.5rem] p-8 shadow-sm border border-slate-100 mb-8">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-xl font-bold text-slate-900">Recommended For You</h2>
        </div>
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="w-full bg-white rounded-[2.5rem] p-8 shadow-sm border border-slate-100 mb-8">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-xl font-bold text-slate-900">Recommended For You</h2>
        </div>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="size-16 rounded-full bg-red-50 flex items-center justify-center mb-4">
            <RefreshCw className="w-8 h-8 text-red-500" />
          </div>
          <p className="text-slate-900 font-medium mb-1">Unable to load videos</p>
          <p className="text-slate-500 text-sm mb-4">{error}</p>
          <button
            onClick={fetchVideos}
            className="px-6 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors font-medium text-sm"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Empty state
  if (videos.length === 0) {
    return (
      <div className="w-full bg-white rounded-[2.5rem] p-8 shadow-sm border border-slate-100 mb-8">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-xl font-bold text-slate-900">Recommended For You</h2>
        </div>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="size-20 rounded-full bg-slate-50 flex items-center justify-center mb-4">
            <span className="material-symbols-outlined text-4xl text-slate-300">videocam_off</span>
          </div>
          <h3 className="text-lg font-semibold text-slate-900">No videos available</h3>
          <p className="text-slate-500 max-w-sm mt-2">
            Check back later for new content from your instructors.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full mb-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 px-2">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-bold text-slate-900">
            Recommended For You
          </h2>
          <span className="px-3 py-1 bg-indigo-50 text-indigo-600 text-xs font-bold rounded-lg border border-indigo-100">
            {videos.length} NEW
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Slider Controls */}
          <div className="flex items-center p-1 bg-white rounded-xl border border-slate-200 shadow-sm">
            <button
              onClick={() => scroll("left")}
              disabled={!canScrollLeft}
              className={`p-1.5 rounded-lg transition-all ${canScrollLeft
                ? "hover:bg-slate-100 text-slate-600"
                : "text-slate-300 cursor-not-allowed"
                }`}
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <div className="w-px h-4 bg-slate-200 mx-1"></div>
            <button
              onClick={() => scroll("right")}
              disabled={!canScrollRight}
              className={`p-1.5 rounded-lg transition-all ${canScrollRight
                ? "hover:bg-slate-100 text-slate-600"
                : "text-slate-300 cursor-not-allowed"
                }`}
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>

          <button className="hidden md:block px-4 py-2 bg-white text-indigo-600 text-sm font-semibold rounded-xl border border-slate-200 shadow-sm hover:bg-slate-50 transition-colors ml-2">
            View All
          </button>
        </div>
      </div>

      {/* Horizontal Slider */}
      <div className="relative group/slider">
        <div
          ref={scrollContainerRef}
          className="flex gap-6 overflow-x-auto pb-8 pt-2 px-2 scrollbar-hide snap-x snap-mandatory"
          style={{
            scrollbarWidth: "none",
            msOverflowStyle: "none",
          }}
        >
          {videos.map((video) => (
            <VideoCard key={video.id} video={video} onPlay={handlePlay} />
          ))}
        </div>

        {/* Gradient fades for scrolling indication */}
        {canScrollLeft && (
          <div className="absolute left-0 top-0 bottom-8 w-24 bg-gradient-to-r from-[#f8fafc] to-transparent pointer-events-none z-10" />
        )}
        {canScrollRight && (
          <div className="absolute right-0 top-0 bottom-8 w-24 bg-gradient-to-l from-[#f8fafc] to-transparent pointer-events-none z-10" />
        )}
      </div>
    </div>
  );
};

export default RecommendedVideos;

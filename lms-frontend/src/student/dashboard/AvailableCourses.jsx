import { useState, useEffect, useRef, useCallback } from "react";
import {
  BookOpen,
  Clock,
  Users,
  Star,
  FileText,
  Video,
  Search,
  Filter,
  ChevronDown,
  Loader2,
  GraduationCap,
  X,
} from "lucide-react";
import studentApi from "../../utils/studentApi";
import CourseContentPreview from "./CourseContentPreview";

const COURSE_CATEGORIES = [
  { value: "", label: "All Categories" },
  { value: "programming", label: "Programming" },
  { value: "web_development", label: "Web Development" },
  { value: "mobile_development", label: "Mobile Development" },
  { value: "data_science", label: "Data Science" },
  { value: "machine_learning", label: "Machine Learning" },
  { value: "design", label: "Design" },
  { value: "business", label: "Business" },
  { value: "marketing", label: "Marketing" },
  { value: "academics", label: "Academics" },
  { value: "other", label: "Other" },
];

const COURSE_LEVELS = [
  { value: "", label: "All Levels" },
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
  { value: "all_levels", label: "All Levels" },
];

const CourseCard = ({ course, onViewContent }) => {
  const getLevelColor = (level) => {
    switch (level) {
      case "beginner":
        return "bg-green-100 text-green-700";
      case "intermediate":
        return "bg-yellow-100 text-yellow-700";
      case "advanced":
        return "bg-red-100 text-red-700";
      default:
        return "bg-blue-100 text-blue-700";
    }
  };

  const formatDuration = (minutes) => {
    if (!minutes) return "N/A";
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  return (      <div className="bg-white rounded-2xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden group">
      {/* Thumbnail */}
      <div className="relative h-44 bg-gradient-to-br from-indigo-500 to-purple-600 overflow-hidden">
        {course.thumbnailUrl ? (
          <img
            src={course.thumbnailUrl}
            alt={course.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <BookOpen className="w-16 h-16 text-white/50" />
          </div>
        )}
        {/* Category badge */}
        <div className="absolute top-3 left-3">
          <span className="px-3 py-1 bg-white/90 backdrop-blur-sm rounded-full text-xs font-medium text-gray-700 capitalize">
            {course.category?.replace("_", " ") || "General"}
          </span>
        </div>
        {/* Level badge */}
        <div className="absolute top-3 right-3">
          <span
            className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${getLevelColor(
              course.level
            )}`}
          >
            {course.level?.replace("_", " ") || "All Levels"}
          </span>
        </div>
        {/* Free/Paid badge */}
        {course.isFree && (
          <div className="absolute bottom-3 left-3">
            <span className="px-3 py-1 bg-green-500 rounded-full text-xs font-bold text-white">
              FREE
            </span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-5">
        {/* Title */}
        <h3 className="font-bold text-gray-900 text-lg mb-2 line-clamp-2 group-hover:text-indigo-600 transition-colors">
          {course.title}
        </h3>

        {/* Subtitle/Description */}
        <p className="text-sm text-gray-500 mb-4 line-clamp-2">
          {course.subtitle || course.description || "No description available"}
        </p>

        {/* Instructor */}
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
            <GraduationCap className="w-4 h-4 text-indigo-600" />
          </div>
          <span className="text-sm text-gray-600">
            {course.instructor?.firstName} {course.instructor?.lastName}
          </span>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
          <div className="flex items-center gap-1">
            <Video className="w-4 h-4" />
            <span>{course.totalVideos || 0} videos</span>
          </div>
          <div className="flex items-center gap-1">
            <FileText className="w-4 h-4" />
            <span>{course.totalDocuments || 0} docs</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            <span>{formatDuration(course.estimatedDuration)}</span>
          </div>
        </div>

        {/* Rating & Enrollment */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <div className="flex items-center gap-1">
            <Star className="w-4 h-4 text-yellow-400 fill-current" />
            <span className="font-medium text-gray-900">
              {course.averageRating
                ? parseFloat(course.averageRating).toFixed(1)
                : "N/A"}
            </span>
            <span className="text-gray-400 text-sm">
              ({course.ratingCount || 0})
            </span>
          </div>
          <div className="flex items-center gap-1 text-gray-500">
            <Users className="w-4 h-4" />
            <span className="text-sm">
              {course.enrollmentCount || 0} enrolled
            </span>
          </div>
        </div>

        {/* Action Button */}
        <button
          onClick={() => onViewContent(course)}
          className="w-full mt-4 py-2.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-600 font-medium rounded-xl transition-colors flex items-center justify-center gap-2"
        >
          <BookOpen className="w-4 h-4" />
          View Course Content
        </button>
      </div>
    </div>
  );
};

const AvailableCourses = ({ onEnrollSuccess }) => {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [level, setLevel] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [totalCourses, setTotalCourses] = useState(0);

  const observerRef = useRef(null);
  const loadingRef = useRef(null);
  const searchTimeoutRef = useRef(null);

  const fetchCourses = useCallback(
    async (pageNum = 1, isNewSearch = false) => {
      if (loading) return;

      setLoading(true);
      try {
        const params = {
          page: pageNum,
          limit: 12,
        };

        if (search.trim()) params.search = search.trim();
        if (category) params.category = category;
        if (level) params.level = level;

        const response = await studentApi.getPublishedCourses(params);

        if (isNewSearch) {
          setCourses(response.courses || []);
        } else {
          setCourses((prev) => [...prev, ...(response.courses || [])]);
        }

        setHasMore(response.hasMore || false);
        setTotalCourses(response.total || 0);
        setPage(pageNum);
      } catch (error) {
        console.error("Failed to fetch courses:", error);
      } finally {
        setLoading(false);
        setInitialLoading(false);
      }
    },
    [search, category, level, loading]
  );

  // Initial load
  useEffect(() => {
    fetchCourses(1, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle filter changes
  useEffect(() => {
    if (!initialLoading) {
      fetchCourses(1, true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category, level]);

  // Handle search with debounce
  const handleSearchChange = (e) => {
    const value = e.target.value;
    setSearch(value);

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    searchTimeoutRef.current = setTimeout(() => {
      fetchCourses(1, true);
    }, 500);
  };

  // Infinite scroll observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          fetchCourses(page + 1, false);
        }
      },
      { threshold: 0.1 }
    );

    if (loadingRef.current) {
      observer.observe(loadingRef.current);
    }

    observerRef.current = observer;

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [hasMore, loading, page, fetchCourses]);

  const handleViewContent = (course) => {
    setSelectedCourse(course);
  };

  const handleClosePreview = () => {
    setSelectedCourse(null);
  };

  const clearFilters = () => {
    setSearch("");
    setCategory("");
    setLevel("");
    fetchCourses(1, true);
  };

  const hasActiveFilters = search || category || level;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            Available Courses
          </h2>
          <p className="text-gray-500 mt-1">
            Explore {totalCourses} courses from our expert instructors
          </p>
        </div>

        {/* Search & Filters */}
        <div className="flex items-center gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={handleSearchChange}
              placeholder="Search courses..."
              className="pl-10 pr-4 py-2.5 w-64 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border transition-colors ${
              showFilters || hasActiveFilters
                ? "bg-indigo-50 border-indigo-200 text-indigo-600"
                : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
            }`}
          >
            <Filter className="w-4 h-4" />
            <span className="text-sm font-medium">Filters</span>
            {hasActiveFilters && (
              <span className="w-2 h-2 bg-indigo-500 rounded-full"></span>
            )}
          </button>
        </div>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 flex flex-wrap items-center gap-4">
          {/* Category Filter */}
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <div className="relative">
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full appearance-none px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 pr-10"
              >
                {COURSE_CATEGORIES.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          {/* Level Filter */}
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Level
            </label>
            <div className="relative">
              <select
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                className="w-full appearance-none px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 pr-10"
              >
                {COURSE_LEVELS.map((lvl) => (
                  <option key={lvl.value} value={lvl.value}>
                    {lvl.label}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          {/* Clear Filters */}
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors mt-6"
            >
              <X className="w-4 h-4" />
              Clear Filters
            </button>
          )}
        </div>
      )}

      {/* Loading State */}
      {initialLoading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-12 h-12 text-indigo-500 animate-spin mb-4" />
          <p className="text-gray-500">Loading courses...</p>
        </div>
      ) : courses.length === 0 ? (
        /* Empty State */
        <div className="flex flex-col items-center justify-center py-20 bg-white rounded-2xl">
          <BookOpen className="w-16 h-16 text-gray-300 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No courses found
          </h3>
          <p className="text-gray-500 text-center max-w-md">
            {hasActiveFilters
              ? "Try adjusting your filters or search query to find more courses."
              : "No published courses are available at the moment. Check back later!"}
          </p>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="mt-4 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Clear Filters
            </button>
          )}
        </div>
      ) : (
        <>
          {/* Courses Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {courses.map((course) => (
              <CourseCard
                key={course.id}
                course={course}
                onViewContent={handleViewContent}
              />
            ))}
          </div>

          {/* Infinite Scroll Loader */}
          <div ref={loadingRef} className="flex justify-center py-8">
            {loading && (
              <div className="flex items-center gap-3 text-gray-500">
                <Loader2 className="w-6 h-6 animate-spin" />
                <span>Loading more courses...</span>
              </div>
            )}
            {!hasMore && courses.length > 0 && (
              <p className="text-gray-400 text-sm">
                You've reached the end of the list
              </p>
            )}
          </div>
        </>
      )}

      {/* Course Content Preview Modal */}
      {selectedCourse && (
        <CourseContentPreview
          course={selectedCourse}
          onClose={handleClosePreview}
          onEnrollSuccess={onEnrollSuccess}
        />
      )}
    </div>
  );
};

export default AvailableCourses;

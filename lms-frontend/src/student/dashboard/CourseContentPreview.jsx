import { useState, useEffect } from "react";
import {
  X,
  Video,
  FileText,
  Clock,
  ChevronDown,
  ChevronUp,
  Play,
  File,
  FileSpreadsheet,
  Presentation,
  BookOpen,
  Eye,
  Lock,
  Loader2,
  GraduationCap,
  Users,
  Star,
} from "lucide-react";
import studentApi from "../../utils/studentApi";

const ContentTypeIcon = ({ type, className = "w-5 h-5" }) => {
  switch (type) {
    case "video":
      return <Video className={`${className} text-blue-500`} />;
    case "document":
      return <FileText className={`${className} text-green-500`} />;
    case "text":
      return <BookOpen className={`${className} text-purple-500`} />;
    default:
      return <File className={`${className} text-gray-500`} />;
  }
};

const DocumentTypeIcon = ({ mimeType, className = "w-5 h-5" }) => {
  if (mimeType?.includes("pdf")) {
    return <FileText className={`${className} text-red-500`} />;
  } else if (mimeType?.includes("word") || mimeType?.includes("document")) {
    return <File className={`${className} text-blue-500`} />;
  } else if (mimeType?.includes("spreadsheet") || mimeType?.includes("excel")) {
    return <FileSpreadsheet className={`${className} text-green-500`} />;
  } else if (
    mimeType?.includes("presentation") ||
    mimeType?.includes("powerpoint")
  ) {
    return <Presentation className={`${className} text-orange-500`} />;
  }
  return <File className={`${className} text-gray-500`} />;
};

const SectionAccordion = ({ section, isOpen, onToggle }) => {
  const videoCount = section.contents.filter(
    (c) => c.contentType === "video"
  ).length;
  const docCount = section.contents.filter(
    (c) => c.contentType === "document"
  ).length;
  const textCount = section.contents.filter(
    (c) => c.contentType === "text"
  ).length;

  return (      <div className="rounded-xl overflow-hidden">
      {/* Section Header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center font-semibold text-sm">
            {section.order}
          </span>
          <div className="text-left">
            <h4 className="font-semibold text-gray-900">{section.title}</h4>
            <div className="flex items-center gap-3 text-xs text-gray-500 mt-1">
              {videoCount > 0 && (
                <span className="flex items-center gap-1">
                  <Video className="w-3.5 h-3.5" /> {videoCount} videos
                </span>
              )}
              {docCount > 0 && (
                <span className="flex items-center gap-1">
                  <FileText className="w-3.5 h-3.5" /> {docCount} docs
                </span>
              )}
              {textCount > 0 && (
                <span className="flex items-center gap-1">
                  <BookOpen className="w-3.5 h-3.5" /> {textCount} texts
                </span>
              )}
            </div>
          </div>
        </div>
        {isOpen ? (
          <ChevronUp className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        )}
      </button>

      {/* Section Contents */}
      {isOpen && (
        <div className="divide-y divide-gray-100">
          {section.contents.map((content) => (
            <div
              key={content.id}
              className="flex items-center gap-4 p-4 hover:bg-gray-50 transition-colors"
            >
              {/* Content Icon */}
              <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
                <ContentTypeIcon type={content.contentType} />
              </div>

              {/* Content Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h5 className="font-medium text-gray-900 truncate">
                    {content.title}
                  </h5>
                  {content.isPreview && (
                    <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full flex items-center gap-1">
                      <Eye className="w-3 h-3" />
                      Preview
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-500 mt-1">
                  <span className="capitalize">{content.contentType}</span>
                  {content.estimatedMinutes && (
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {content.estimatedMinutes} min
                    </span>
                  )}
                </div>
              </div>

              {/* Preview/Lock indicator */}
              <div className="flex-shrink-0">
                {content.isPreview ? (
                  <button className="p-2 rounded-full bg-indigo-50 text-indigo-600 hover:bg-indigo-100 transition-colors">
                    <Play className="w-4 h-4" />
                  </button>
                ) : (
                  <div className="p-2 rounded-full bg-gray-100 text-gray-400">
                    <Lock className="w-4 h-4" />
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const CourseContentPreview = ({ course, onClose, onEnrollSuccess }) => {
  const [contentSummary, setContentSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState(false);
  const [error, setError] = useState(null);
  const [expandedSections, setExpandedSections] = useState({});

  useEffect(() => {
    const fetchContentSummary = async () => {
      try {
        setLoading(true);
        const data = await studentApi.getCourseContentSummary(course.id);
        setContentSummary(data);
        // Expand first section by default
        if (data.sections?.length > 0) {
          setExpandedSections({ [data.sections[0].id]: true });
        }
      } catch (err) {
        console.error("Failed to fetch content summary:", err);
        setError("Failed to load course content. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchContentSummary();
  }, [course.id]);

  const toggleSection = (sectionId) => {
    setExpandedSections((prev) => ({
      ...prev,
      [sectionId]: !prev[sectionId],
    }));
  };

  const expandAll = () => {
    const allExpanded = {};
    contentSummary?.sections?.forEach((s) => {
      allExpanded[s.id] = true;
    });
    setExpandedSections(allExpanded);
  };

  const collapseAll = () => {
    setExpandedSections({});
  };

  const formatDuration = (minutes) => {
    if (!minutes) return "N/A";
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins} minutes`;
  };

  const handleEnroll = async () => {
    try {
      setEnrolling(true);
      setError(null);
      await studentApi.enrollInCourse(course.id);
      // Notify parent about successful enrollment
      if (onEnrollSuccess) {
        onEnrollSuccess(course);
      }
      onClose();
    } catch (err) {
      console.error("Failed to enroll:", err);
      setError(err.message || "Failed to enroll in course. Please try again.");
    } finally {
      setEnrolling(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 flex-shrink-0">
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                {course.title}
              </h2>
              <p className="text-gray-500 text-sm line-clamp-2 mb-3">
                {course.subtitle || course.description}
              </p>

              {/* Instructor Info */}
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <GraduationCap className="w-4 h-4 text-indigo-500" />
                  <span className="text-gray-600">
                    {course.instructor?.firstName} {course.instructor?.lastName}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-gray-500">
                  <Star className="w-4 h-4 text-yellow-400 fill-current" />
                  <span>
                    {course.averageRating
                      ? parseFloat(course.averageRating).toFixed(1)
                      : "N/A"}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-gray-500">
                  <Users className="w-4 h-4" />
                  <span>{course.enrollmentCount || 0} enrolled</span>
                </div>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-xl transition-colors ml-4"
            >
              <X className="w-6 h-6 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Content Summary Stats */}
        {!loading && contentSummary && (
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex-shrink-0">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-3 p-3 bg-white rounded-xl">
                <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                  <BookOpen className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    {contentSummary.totalSections}
                  </p>
                  <p className="text-xs text-gray-500">Sections</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-white rounded-xl">
                <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                  <Video className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    {contentSummary.totalVideos}
                  </p>
                  <p className="text-xs text-gray-500">Videos</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-white rounded-xl">
                <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    {contentSummary.totalDocuments}
                  </p>
                  <p className="text-xs text-gray-500">Documents</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-white rounded-xl">
                <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-orange-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatDuration(contentSummary.totalEstimatedMinutes)}
                  </p>
                  <p className="text-xs text-gray-500">Total Duration</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-10 h-10 text-indigo-500 animate-spin mb-4" />
              <p className="text-gray-500">Loading course content...</p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-4">
                <X className="w-8 h-8 text-red-500" />
              </div>
              <p className="text-gray-900 font-medium mb-2">
                Error Loading Content
              </p>
              <p className="text-gray-500 text-sm">{error}</p>
            </div>
          ) : contentSummary?.sections?.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <BookOpen className="w-16 h-16 text-gray-300 mb-4" />
              <p className="text-gray-900 font-medium mb-2">No Content Yet</p>
              <p className="text-gray-500 text-sm">
                This course doesn't have any content sections yet.
              </p>
            </div>
          ) : (
            <>
              {/* Expand/Collapse Controls */}
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">Course Content</h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={expandAll}
                    className="text-sm text-indigo-600 hover:text-indigo-700"
                  >
                    Expand All
                  </button>
                  <span className="text-gray-300">|</span>
                  <button
                    onClick={collapseAll}
                    className="text-sm text-indigo-600 hover:text-indigo-700"
                  >
                    Collapse All
                  </button>
                </div>
              </div>

              {/* Sections */}
              <div className="space-y-3">
                {contentSummary.sections.map((section) => (
                  <SectionAccordion
                    key={section.id}
                    section={section}
                    isOpen={expandedSections[section.id] || false}
                    onToggle={() => toggleSection(section.id)}
                  />
                ))}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 flex-shrink-0 bg-gray-50">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              {course.isFree ? (
                <span className="text-green-600 font-semibold">
                  Free Course
                </span>
              ) : (
                <span>
                  Price:{" "}
                  <span className="font-semibold text-gray-900">
                    {course.currency || "INR"} {course.price || "N/A"}
                  </span>
                </span>
              )}
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={onClose}
                className="px-6 py-2.5 text-gray-600 font-medium rounded-xl hover:bg-gray-100 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleEnroll}
                disabled={enrolling}
                className="px-6 py-2.5 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {enrolling ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Enrolling...
                  </>
                ) : (
                  "Enroll Now"
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CourseContentPreview;

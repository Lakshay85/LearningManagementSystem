import { useState, useEffect } from "react";
import {
  BookOpen,
  Plus,
  Search,
  Filter,
  MoreVertical,
  Edit,
  Trash2,
  Eye,
  Users,
  FileText,
  Video,
  Clock,
  AlertCircle,
  Loader2,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Send,
  Archive,
  FileEdit,
  Globe,
} from "lucide-react";
import facultyApi from "../../utils/facultyApi";
import CustomSelect from "../../components/common/CustomSelect";

// Grid Pattern SVG component
const GridPattern = () => (
  <svg className="absolute inset-0 w-full h-full opacity-10" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
        <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="1" />
      </pattern>
    </defs>
    <rect width="100%" height="100%" fill="url(#grid)" />
  </svg>
);

// Status badge component
const StatusBadge = ({ status }) => {
  const statusStyles = {
    draft: "bg-white/90 backdrop-blur-sm text-slate-800",
    pending_review: "bg-amber-100/90 backdrop-blur-sm text-amber-800",
    published: "bg-emerald-100/90 backdrop-blur-sm text-emerald-800",
    archived: "bg-red-100/90 backdrop-blur-sm text-red-800",
  };

  const statusLabels = {
    draft: "Draft",
    pending_review: "Pending Review",
    published: "Published",
    archived: "Archived",
  };

  return (
    <span
      className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider ${statusStyles[status] || statusStyles.draft
        }`}
    >
      {statusLabels[status] || status}
    </span>
  );
};

// Course card component
const CourseCard = ({ course, onEdit, onDelete, onView, onStatusChange }) => {
  const [showMenu, setShowMenu] = useState(false);
  const [showStatusMenu, setShowStatusMenu] = useState(false);

  const statusOptions = [
    { value: "draft", label: "Draft", icon: FileEdit, color: "text-slate-600" },
    {
      value: "pending_review",
      label: "Submit for Review",
      icon: Send,
      color: "text-amber-600",
    },
    {
      value: "published",
      label: "Publish",
      icon: Globe,
      color: "text-emerald-600",
    },
    {
      value: "archived",
      label: "Archive",
      icon: Archive,
      color: "text-red-600",
    },
  ];

  // Filter out current status from options
  const availableStatuses = statusOptions.filter(
    (s) => s.value !== course.status
  );

  return (
    <div className="bg-white rounded-2xl border border-slate-100 relative group transition-all duration-300 hover:shadow-[0_20px_40px_-15px_rgba(0,0,0,0.1)]"
      style={{ boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05)' }}
    >
      {/* Thumbnail with Grid Pattern */}
      <div className="relative h-48 bg-emerald-500 flex items-center justify-center overflow-hidden rounded-t-2xl">
        <GridPattern />
        {course.thumbnailUrl ? (
          <img
            src={course.thumbnailUrl}
            alt={course.title}
            className="w-full h-full object-cover relative z-10"
          />
        ) : (
          <div className="relative z-10 text-white/90">
            <BookOpen className="w-16 h-16" strokeWidth={1.5} />
          </div>
        )}
        <div className="absolute top-4 right-4 z-20">
          <StatusBadge status={course.status} />
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        <div className="flex justify-between items-start mb-2">
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight line-clamp-2 flex-1">
            {course.title}
          </h2>
          <div className="relative ml-2">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="p-1 text-slate-400 hover:text-slate-600 rounded-full transition-colors"
            >
              <MoreVertical className="w-5 h-5" />
            </button>
            {showMenu && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => {
                    setShowMenu(false);
                    setShowStatusMenu(false);
                  }}
                />
                <div className="absolute right-0 top-10 w-56 bg-white rounded-xl shadow-2xl border border-slate-200 z-20 overflow-hidden">
                  <div className="p-1">
                    <button
                      onClick={() => {
                        onView(course);
                        setShowMenu(false);
                      }}
                      className="w-full px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50 rounded-lg flex items-center gap-3 transition-colors group/item"
                    >
                      <Eye className="w-5 h-5 text-slate-400 group-hover/item:text-emerald-500 transition-colors" />
                      View
                    </button>
                    <button
                      onClick={() => {
                        onEdit(course);
                        setShowMenu(false);
                      }}
                      className="w-full px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50 rounded-lg flex items-center gap-3 transition-colors group/item"
                    >
                      <Edit className="w-5 h-5 text-slate-400 group-hover/item:text-emerald-500 transition-colors" />
                      Edit
                    </button>

                    {/* Status Change Section */}
                    <div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowStatusMenu(!showStatusMenu);
                        }}
                        className="w-full px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50 rounded-lg flex items-center justify-between transition-colors group/item"
                      >
                        <div className="flex items-center gap-3">
                          <Globe className="w-5 h-5 text-slate-400 group-hover/item:text-emerald-500 transition-colors" />
                          Change Status
                        </div>
                        <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${showStatusMenu ? 'rotate-180' : ''}`} />
                      </button>
                      {showStatusMenu && (
                        <div className="py-1 pl-8 space-y-0.5">
                          {availableStatuses.map((status) => (
                            <button
                              key={status.value}
                              onClick={() => {
                                onStatusChange(course, status.value);
                                setShowMenu(false);
                                setShowStatusMenu(false);
                              }}
                              className={`w-full px-3 py-2 text-left text-sm rounded-lg flex items-center gap-3 transition-colors ${status.value === 'pending_review'
                                  ? 'text-amber-600 hover:bg-amber-50'
                                  : status.value === 'published'
                                    ? 'text-emerald-600 hover:bg-emerald-50'
                                    : status.value === 'archived'
                                      ? 'text-red-600 hover:bg-red-50'
                                      : 'text-slate-600 hover:bg-slate-50'
                                }`}
                            >
                              <status.icon className="w-4 h-4" />
                              {status.label}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="h-px bg-slate-100 my-1" />
                    <button
                      onClick={() => {
                        onDelete(course);
                        setShowMenu(false);
                      }}
                      className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 rounded-lg flex items-center gap-3 transition-colors"
                    >
                      <Trash2 className="w-5 h-5 text-red-500" />
                      Delete
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        <p className="text-slate-500 text-sm mb-6 line-clamp-2">
          {course.subtitle || course.description || "No description provided for this course yet."}
        </p>

        {/* Stats */}
        <div className="flex flex-wrap gap-4 mb-6">
          <div className="flex items-center text-slate-500">
            <Users className="w-[18px] h-[18px] mr-1.5" />
            <span className="text-sm font-medium">{course.enrollmentCount || 0} students</span>
          </div>
          <div className="flex items-center text-slate-500">
            <Video className="w-[18px] h-[18px] mr-1.5" />
            <span className="text-sm font-medium">{course.totalVideos || 0} videos</span>
          </div>
          <div className="flex items-center text-slate-500">
            <FileText className="w-[18px] h-[18px] mr-1.5" />
            <span className="text-sm font-medium">{course.totalDocuments || 0} docs</span>
          </div>
        </div>

        {/* Category & Level */}
        <div className="flex gap-2 mb-8">
          <span className="px-3 py-1 bg-emerald-50 text-emerald-600 text-xs font-semibold rounded-full border border-emerald-100">
            {course.category?.replace(/_/g, " ") || "Other"}
          </span>
          <span className="px-3 py-1 bg-blue-50 text-blue-600 text-xs font-semibold rounded-full border border-blue-100">
            {course.level?.replace(/_/g, " ") || "Beginner"}
          </span>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between text-slate-400 text-xs border-t border-slate-100 pt-4">
          <div className="flex items-center">
            <Clock className="w-4 h-4 mr-1" />
            <span>
              Created{" "}
              {new Date(course.createdAt).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
              })}
            </span>
          </div>
          {course.isFree ? (
            <span className="text-sm font-semibold text-emerald-600">Free</span>
          ) : (
            <span className="text-sm font-semibold text-slate-700">
              {course.currency} {course.price || 0}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

// Empty state component
const EmptyState = ({ onCreateCourse }) => (
  <div className="flex flex-col items-center justify-center py-16">
    <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mb-4">
      <BookOpen className="w-10 h-10 text-emerald-600" />
    </div>
    <h3 className="text-xl font-semibold text-gray-900 mb-2">No courses yet</h3>
    <p className="text-gray-500 text-center mb-6 max-w-md">
      Start creating your first course to share your knowledge with students.
    </p>
    <button
      onClick={onCreateCourse}
      className="flex items-center gap-2 px-6 py-3 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition-colors"
    >
      <Plus className="w-5 h-5" />
      Create Your First Course
    </button>
  </div>
);

function MyCourses({ setActiveTab, setEditingCourse }) {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [statusChangeConfirm, setStatusChangeConfirm] = useState(null);
  const [changingStatus, setChangingStatus] = useState(false);

  // Fetch courses
  const fetchCourses = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await facultyApi.getMyCourses();
      setCourses(response.data || response || []);
    } catch (err) {
      console.error("Error fetching courses:", err);
      setError("Failed to load courses. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, []);

  // Filter courses
  const filteredCourses = courses.filter((course) => {
    const matchesSearch =
      course.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      course.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus =
      statusFilter === "all" || course.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Handle create course
  const handleCreateCourse = () => {
    if (setEditingCourse) {
      setEditingCourse(null);
    }
    setActiveTab("course-create");
  };

  // Handle edit course
  const handleEditCourse = (course) => {
    if (setEditingCourse) {
      setEditingCourse(course);
    }
    setActiveTab("course-create");
  };

  // Handle view course
  const handleViewCourse = (course) => {
    // For now, just edit it. Can add a view mode later
    handleEditCourse(course);
  };

  // Handle delete course
  const handleDeleteCourse = async (course) => {
    setDeleteConfirm(course);
  };

  const confirmDelete = async () => {
    if (!deleteConfirm) return;

    try {
      setDeleting(true);
      await facultyApi.deleteCourse(deleteConfirm.id);
      setCourses(courses.filter((c) => c.id !== deleteConfirm.id));
      setDeleteConfirm(null);
    } catch (err) {
      console.error("Error deleting course:", err);
      alert("Failed to delete course. Please try again.");
    } finally {
      setDeleting(false);
    }
  };

  // Handle status change
  const handleStatusChange = (course, newStatus) => {
    setStatusChangeConfirm({ course, newStatus });
  };

  const confirmStatusChange = async () => {
    if (!statusChangeConfirm) return;

    const { course, newStatus } = statusChangeConfirm;

    try {
      setChangingStatus(true);
      await facultyApi.updateCourse(course.id, { status: newStatus });
      setCourses(
        courses.map((c) =>
          c.id === course.id ? { ...c, status: newStatus } : c
        )
      );
      setStatusChangeConfirm(null);
    } catch (err) {
      console.error("Error changing course status:", err);
      alert("Failed to change course status. Please try again.");
    } finally {
      setChangingStatus(false);
    }
  };

  const getStatusLabel = (status) => {
    const labels = {
      draft: "Draft",
      pending_review: "Pending Review",
      published: "Published",
      archived: "Archived",
    };
    return labels[status] || status;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={fetchCourses}
          className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Courses</h1>
          <p className="text-gray-500 mt-1">
            Manage and organize your course content
          </p>
        </div>
        <button
          onClick={handleCreateCourse}
          className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Create New Course
        </button>
      </div>

      {courses.length === 0 ? (
        <EmptyState onCreateCourse={handleCreateCourse} />
      ) : (
        <>
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search courses..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            {/* Status Filter */}
            <div className="w-48">
              <CustomSelect
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                icon={Filter}
                className="border border-gray-200 rounded-xl"
              >
                <option value="all">All Status</option>
                <option value="draft">Draft</option>
                <option value="pending_review">Pending Review</option>
                <option value="published">Published</option>
                <option value="archived">Archived</option>
              </CustomSelect>
            </div>
          </div>

          {/* Course Grid */}
          {filteredCourses.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">
                No courses match your search criteria.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredCourses.map((course) => (
                <CourseCard
                  key={course.id}
                  course={course}
                  onEdit={handleEditCourse}
                  onDelete={handleDeleteCourse}
                  onView={handleViewCourse}
                  onStatusChange={handleStatusChange}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Delete Course
            </h3>
            <p className="text-gray-500 mb-6">
              Are you sure you want to delete "{deleteConfirm.title}"? This
              action cannot be undone and will remove all sections and content.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setDeleteConfirm(null)}
                disabled={deleting}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleting}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {deleting && <Loader2 className="w-4 h-4 animate-spin" />}
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Status Change Confirmation Modal */}
      {statusChangeConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Change Course Status
            </h3>
            <p className="text-gray-500 mb-4">
              Are you sure you want to change the status of "
              {statusChangeConfirm.course.title}" from{" "}
              <span className="font-medium">
                {getStatusLabel(statusChangeConfirm.course.status)}
              </span>{" "}
              to{" "}
              <span className="font-medium">
                {getStatusLabel(statusChangeConfirm.newStatus)}
              </span>
              ?
            </p>
            {statusChangeConfirm.newStatus === "published" && (
              <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  <strong>Note:</strong> Publishing this course will make it
                  visible to students based on your visibility settings.
                </p>
              </div>
            )}
            {statusChangeConfirm.newStatus === "archived" && (
              <div className="mb-4 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                <p className="text-sm text-orange-800">
                  <strong>Note:</strong> Archiving this course will hide it from
                  new students, but existing enrollments will remain.
                </p>
              </div>
            )}
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setStatusChangeConfirm(null)}
                disabled={changingStatus}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={confirmStatusChange}
                disabled={changingStatus}
                className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
              >
                {changingStatus && <Loader2 className="w-4 h-4 animate-spin" />}
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default MyCourses;

import { useState, useEffect } from "react";
import ConfirmationModal from "../../../components/common/ConfirmationModal";
import {
  HelpCircle,
  Plus,
  Sparkles,
  Search,
  Filter,
  MoreVertical,
  Edit2,
  Trash2,
  Eye,
  Send,
  Archive,
  Users,
  CheckCircle2,
  Clock,
  AlertCircle,
  BookOpen,
  Loader2
} from "lucide-react";
import facultyApi from "../../../utils/facultyApi";
import CustomSelect from "../../../components/common/CustomSelect";
import QuizAIGenerator from "./QuizAIGenerator";

export default function QuizManager({ setActiveTab, setEditingQuizId, setViewingQuizId }) {
  const [courses, setCourses] = useState([]);
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [quizzes, setQuizzes] = useState([]);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [loadingQuizzes, setLoadingQuizzes] = useState(false);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // Modals & Menu
  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newQuizTitle, setNewQuizTitle] = useState("");
  const [newQuizDesc, setNewQuizDesc] = useState("");
  const [creatingBlank, setCreatingBlank] = useState(false);
  const [activeMenuQuizId, setActiveMenuQuizId] = useState(null);
  const [confirmAction, setConfirmAction] = useState(null);

  // 1. Fetch faculty courses
  useEffect(() => {
    const fetchCourses = async () => {
      try {
        setLoadingCourses(true);
        const res = await facultyApi.getMyCourses();
        const courseList = res?.data || res || [];
        setCourses(courseList);
        if (courseList.length > 0) {
          setSelectedCourseId(courseList[0].id);
        }
      } catch (err) {
        console.error("Failed to load courses:", err);
        setError("Failed to load courses.");
      } finally {
        setLoadingCourses(false);
      }
    };
    fetchCourses();
  }, []);

  // 2. Fetch quizzes when selected course changes
  const fetchQuizzes = async (courseId) => {
    if (!courseId) return;
    try {
      setLoadingQuizzes(true);
      setError("");
      const res = await facultyApi.getCourseQuizzes(courseId);
      setQuizzes(res?.data || res || []);
    } catch (err) {
      console.error("Failed to load quizzes:", err);
      setError("Failed to load quizzes for this course.");
    } finally {
      setLoadingQuizzes(false);
    }
  };

  useEffect(() => {
    if (selectedCourseId) {
      fetchQuizzes(selectedCourseId);
    }
  }, [selectedCourseId]);

  // Handle Create Blank Quiz
  const handleCreateBlankQuiz = async (e) => {
    e.preventDefault();
    if (!newQuizTitle.trim()) return;

    try {
      setCreatingBlank(true);
      const res = await facultyApi.createQuiz({
        courseId: selectedCourseId,
        title: newQuizTitle.trim(),
        description: newQuizDesc.trim() || null,
        passingScore: 60,
      });
      const created = res?.data || res;
      setIsCreateModalOpen(false);
      setNewQuizTitle("");
      setNewQuizDesc("");
      if (setEditingQuizId) setEditingQuizId(created.id);
      setActiveTab("quiz-builder");
    } catch (err) {
      alert(err?.response?.data?.detail || "Failed to create quiz");
    } finally {
      setCreatingBlank(false);
    }
  };

  // Handle Publish / Archive / Delete
  const handlePublishQuiz = async (quizId) => {
    try {
      await facultyApi.publishQuiz(quizId);
      fetchQuizzes(selectedCourseId);
    } catch (err) {
      alert(err?.response?.data?.detail || "Failed to publish quiz");
    }
  };

  const handleArchiveQuiz = (quizId) => {
    setConfirmAction({
      type: "archive",
      quizId,
      title: "Archive Quiz",
      message: "Archive this quiz? It will no longer accept student submissions.",
      confirmText: "Archive",
      isDanger: false
    });
  };

  const handleDeleteQuiz = (quizId) => {
    setConfirmAction({
      type: "delete",
      quizId,
      title: "Delete Quiz",
      message: "Are you sure you want to delete this quiz? This action cannot be undone.",
      confirmText: "Delete",
      isDanger: true
    });
  };

  const executeConfirmAction = async () => {
    if (!confirmAction) return;
    try {
      if (confirmAction.type === "delete") {
        await facultyApi.deleteQuiz(confirmAction.quizId);
      } else if (confirmAction.type === "archive") {
        await facultyApi.archiveQuiz(confirmAction.quizId);
      }
      fetchQuizzes(selectedCourseId);
    } catch (err) {
      alert(err?.response?.data?.detail || `Failed to ${confirmAction.type} quiz`);
    } finally {
      setConfirmAction(null);
    }
  };

  // Filter quizzes
  const filteredQuizzes = quizzes.filter((q) => {
    const matchesSearch =
      q.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      q.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || q.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalCount = quizzes.length;
  const publishedCount = quizzes.filter((q) => q.status === "published").length;
  const draftCount = quizzes.filter((q) => q.status === "draft").length;
  const archivedCount = quizzes.filter((q) => q.status === "archived").length;

  const statusStyles = {
    draft: "bg-amber-50 text-amber-700 border-amber-200",
    published: "bg-emerald-50 text-emerald-700 border-emerald-200",
    archived: "bg-rose-50 text-rose-700 border-rose-200",
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-16 animate-fadeIn">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-gray-900">
            Quizzes & Assessments
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Build AI-generated quizzes grounded in uploaded documents, edit questions, and track student results.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsAiModalOpen(true)}
            disabled={!selectedCourseId}
            className="flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-white bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-700 hover:from-emerald-700 hover:to-teal-700 rounded-2xl shadow-md shadow-emerald-600/20 transition disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-amber-200 animate-pulse" />
            Generate with AI
          </button>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            disabled={!selectedCourseId}
            className="flex items-center gap-2 px-4 py-2.5 text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 border border-gray-200 rounded-2xl shadow-sm transition disabled:opacity-50"
          >
            <Plus className="w-4 h-4 text-emerald-600" />
            Create Blank
          </button>
        </div>
      </div>

      {/* Course Selection & Filter Toolbar */}
      <div className="p-5 rounded-3xl bg-white border border-gray-100 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Course Selector */}
          <div className="flex items-center gap-3 min-w-[280px]">
            <BookOpen className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <div className="flex-1">
              <label className="block text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-0.5">
                Select Course
              </label>
              {loadingCourses ? (
                <div className="text-xs text-gray-400">Loading courses...</div>
              ) : courses.length === 0 ? (
                <div className="text-xs text-amber-600 font-medium">No courses found</div>
              ) : (
                <CustomSelect
                  value={selectedCourseId}
                  onChange={(e) => setSelectedCourseId(e.target.value)}
                  size="sm"
                  className="bg-gray-50 border-gray-200"
                >
                  {courses.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.title}
                    </option>
                  ))}
                </CustomSelect>
              )}
            </div>
          </div>

          {/* Search Bar */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search quizzes by title or keywords..."
              className="w-full pl-10 pr-4 py-2 text-xs bg-gray-50/70 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center justify-between border-t border-gray-100 pt-3 text-xs">
          <div className="flex items-center gap-2">
            {[
              { id: "all", label: "All Quizzes", count: totalCount },
              { id: "published", label: "Published", count: publishedCount },
              { id: "draft", label: "Drafts", count: draftCount },
              { id: "archived", label: "Archived", count: archivedCount },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-semibold transition ${
                  statusFilter === tab.id
                    ? "bg-emerald-50 text-emerald-700"
                    : "text-gray-500 hover:text-gray-800 hover:bg-gray-50"
                }`}
              >
                <span>{tab.label}</span>
                <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-white border border-gray-200">
                  {tab.count}
                </span>
              </button>
            ))}
          </div>

          <span className="text-[11px] text-gray-400 font-medium">
            Showing {filteredQuizzes.length} of {totalCount}
          </span>
        </div>
      </div>

      {/* Quizzes Grid */}
      {loadingQuizzes ? (
        <div className="flex flex-col items-center justify-center min-h-[300px]">
          <Loader2 className="w-8 h-8 text-emerald-600 animate-spin mb-3" />
          <p className="text-xs text-gray-500 font-medium">Loading course quizzes...</p>
        </div>
      ) : filteredQuizzes.length === 0 ? (
        <div className="p-16 text-center bg-white rounded-3xl border border-gray-100 shadow-sm">
          <HelpCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-gray-800">No quizzes found</h3>
          <p className="text-xs text-gray-400 mt-1 mb-5 max-w-sm mx-auto">
            {searchQuery
              ? "No quizzes matched your search query. Try changing your search keywords."
              : "There are no quizzes created for this course yet. Use AI generation or create one manually!"}
          </p>
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={() => setIsAiModalOpen(true)}
              className="flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-sm transition"
            >
              <Sparkles className="w-4 h-4 text-amber-200" />
              Generate with AI
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredQuizzes.map((q) => (
            <div
              key={q.id}
              className="p-6 rounded-3xl bg-white border border-gray-100 shadow-sm hover:shadow-md hover:border-gray-200 transition-all flex flex-col justify-between space-y-4 group"
            >
              <div>
                {/* Status + Menu */}
                <div className="flex items-center justify-between mb-3 relative">
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                      statusStyles[q.status] || statusStyles.draft
                    }`}
                  >
                    {q.status}
                  </span>

                  <div className="relative">
                    <button
                      onClick={() =>
                        setActiveMenuQuizId(activeMenuQuizId === q.id ? null : q.id)
                      }
                      className="p-1.5 text-gray-400 hover:text-gray-700 rounded-lg hover:bg-gray-100"
                    >
                      <MoreVertical className="w-4 h-4" />
                    </button>

                    {activeMenuQuizId === q.id && (
                      <div className="absolute right-0 top-8 z-30 w-44 bg-white rounded-2xl shadow-xl border border-gray-100 p-1 text-xs animate-fadeIn">
                        {q.status === "draft" && (
                          <button
                            onClick={() => {
                              handlePublishQuiz(q.id);
                              setActiveMenuQuizId(null);
                            }}
                            className="w-full text-left px-3 py-2 text-emerald-700 hover:bg-emerald-50 rounded-xl flex items-center gap-2"
                          >
                            <Send className="w-3.5 h-3.5" /> Publish Quiz
                          </button>
                        )}
                        {q.status === "published" && (
                          <button
                            onClick={() => {
                              handleArchiveQuiz(q.id);
                              setActiveMenuQuizId(null);
                            }}
                            className="w-full text-left px-3 py-2 text-amber-700 hover:bg-amber-50 rounded-xl flex items-center gap-2"
                          >
                            <Archive className="w-3.5 h-3.5" /> Archive Quiz
                          </button>
                        )}
                        <button
                          onClick={() => {
                            handleDeleteQuiz(q.id);
                            setActiveMenuQuizId(null);
                          }}
                          className="w-full text-left px-3 py-2 text-rose-600 hover:bg-rose-50 rounded-xl flex items-center gap-2"
                        >
                          <Trash2 className="w-3.5 h-3.5" /> Delete Quiz
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <h3 className="text-base font-bold text-gray-900 group-hover:text-emerald-600 transition line-clamp-2">
                  {q.title}
                </h3>
                <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                  {q.description || "No specific instructions provided."}
                </p>
              </div>

              {/* Meta information */}
              <div className="space-y-4 pt-3 border-t border-gray-100">
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span className="font-semibold text-gray-700">
                    {q.totalQuestions || (q.questions ? q.questions.length : 0)} Questions
                  </span>
                  <span>Passing: {q.passingScore || 60}%</span>
                </div>

                {/* Card Actions */}
                <div className="grid grid-cols-2 gap-2 pt-1">
                  <button
                    onClick={() => {
                      if (setEditingQuizId) setEditingQuizId(q.id);
                      setActiveTab("quiz-builder");
                    }}
                    className="flex items-center justify-center gap-1.5 py-2 px-3 text-xs font-semibold text-gray-700 bg-gray-50 hover:bg-gray-100 rounded-xl transition"
                  >
                    <Edit2 className="w-3.5 h-3.5" /> Edit Quiz
                  </button>

                  <button
                    onClick={() => {
                      if (setViewingQuizId) setViewingQuizId(q.id);
                      setActiveTab("quiz-submissions");
                    }}
                    className="flex items-center justify-center gap-1.5 py-2 px-3 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-xl transition"
                  >
                    <Users className="w-3.5 h-3.5" /> Submissions
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* AI Modal */}
      <QuizAIGenerator
        isOpen={isAiModalOpen}
        onClose={() => setIsAiModalOpen(false)}
        onSuccess={(newQuiz) => {
          fetchQuizzes(selectedCourseId);
          if (setEditingQuizId) setEditingQuizId(newQuiz.id);
          setActiveTab("quiz-builder");
        }}
        initialCourseId={selectedCourseId}
        courses={courses}
      />

      {/* Create Blank Quiz Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white rounded-3xl shadow-2xl border border-gray-100 max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-gray-900">Create Blank Quiz</h3>
            <form onSubmit={handleCreateBlankQuiz} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Quiz Title *</label>
                <input
                  type="text"
                  value={newQuizTitle}
                  onChange={(e) => setNewQuizTitle(e.target.value)}
                  placeholder="e.g. Midterm Practice Exam"
                  className="w-full px-3 py-2 text-sm rounded-xl border border-gray-200 focus:ring-2 focus:ring-emerald-500"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Description</label>
                <textarea
                  rows={2}
                  value={newQuizDesc}
                  onChange={(e) => setNewQuizDesc(e.target.value)}
                  placeholder="Instructions for students..."
                  className="w-full px-3 py-2 text-sm rounded-xl border border-gray-200 focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-4 py-2 text-xs font-medium text-gray-600 hover:bg-gray-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingBlank}
                  className="px-5 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-sm disabled:opacity-50"
                >
                  {creatingBlank ? "Creating..." : "Create & Edit"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <ConfirmationModal
        isOpen={!!confirmAction}
        onClose={() => setConfirmAction(null)}
        onConfirm={executeConfirmAction}
        title={confirmAction?.title || "Confirm"}
        message={confirmAction?.message || "Are you sure?"}
        confirmText={confirmAction?.confirmText || "Confirm"}
        cancelText="Cancel"
        isDanger={confirmAction?.isDanger || false}
      />
    </div>
  );
}

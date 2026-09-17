import { useState, useEffect } from "react";
import {
  ArrowLeft,
  Plus,
  Sparkles,
  Eye,
  Send,
  Trash2,
  Edit2,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ChevronUp,
  ChevronDown,
  Archive,
  Save,
  Users,
  Loader2
} from "lucide-react";
import facultyApi from "../../../utils/facultyApi";
import QuestionEditor from "./QuestionEditor";
import QuizAIGenerator from "./QuizAIGenerator";
import QuizPreview from "./QuizPreview";

export default function QuizBuilder({ quizId, setActiveTab, setViewingQuizId }) {
  const [quiz, setQuiz] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Metadata form
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [passingScore, setPassingScore] = useState(60);
  const [savingMeta, setSavingMeta] = useState(false);

  // Sub-views & modals
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [isQuestionEditorOpen, setIsQuestionEditorOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // Fetch quiz details
  const fetchQuiz = async () => {
    try {
      setLoading(true);
      setError("");
      const res = await facultyApi.getQuiz(quizId);
      const data = res?.data || res;
      setQuiz(data);
      setTitle(data.title || "");
      setDescription(data.description || "");
      setPassingScore(data.passingScore || 60);
    } catch (err) {
      console.error("Error fetching quiz:", err);
      setError("Failed to load quiz. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (quizId) {
      fetchQuiz();
    }
  }, [quizId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 text-emerald-600 animate-spin mb-3" />
        <p className="text-sm text-gray-500 font-medium">Loading quiz builder...</p>
      </div>
    );
  }

  if (error && !quiz) {
    return (
      <div className="p-8 max-w-xl mx-auto bg-white rounded-3xl border border-gray-100 shadow-sm text-center">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto mb-3" />
        <h3 className="text-base font-bold text-gray-900">{error}</h3>
        <button
          onClick={() => setActiveTab("quizzes")}
          className="mt-4 px-5 py-2 text-xs font-semibold text-gray-700 bg-gray-100 rounded-xl hover:bg-gray-200"
        >
          Back to Quizzes
        </button>
      </div>
    );
  }

  // Switch to preview mode if requested
  if (isPreviewOpen) {
    return <QuizPreview quiz={quiz} onBack={() => setIsPreviewOpen(false)} />;
  }

  // Handle Metadata save
  const handleSaveMetadata = async () => {
    try {
      setSavingMeta(true);
      setError("");
      await facultyApi.updateQuiz(quizId, {
        title: title.trim(),
        description: description.trim() || null,
        passingScore: Number(passingScore) || null,
      });
      setSuccessMsg("Quiz details updated successfully.");
      setTimeout(() => setSuccessMsg(""), 3000);
      fetchQuiz();
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to update quiz metadata.");
    } finally {
      setSavingMeta(false);
    }
  };

  // Handle Question Add/Edit
  const handleSaveQuestion = async (questionData) => {
    if (editingQuestion) {
      await facultyApi.updateQuestion(editingQuestion.id, questionData);
    } else {
      await facultyApi.addQuestion(quizId, questionData);
    }
    setEditingQuestion(null);
    setIsQuestionEditorOpen(false);
    fetchQuiz();
  };

  // Handle Question Delete
  const handleDeleteQuestion = async (questionId) => {
    if (!window.confirm("Are you sure you want to delete this question?")) return;
    try {
      await facultyApi.deleteQuestion(questionId);
      fetchQuiz();
    } catch (err) {
      alert(err?.response?.data?.detail || "Failed to delete question");
    }
  };

  // Handle Question Reordering (Move Up / Down)
  const handleMoveQuestion = async (index, direction) => {
    const questions = [...(quiz.questions || [])];
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= questions.length) return;

    const currentQ = questions[index];
    const targetQ = questions[targetIndex];

    try {
      await Promise.all([
        facultyApi.updateQuestion(currentQ.id, { order: targetIndex }),
        facultyApi.updateQuestion(targetQ.id, { order: index }),
      ]);
      fetchQuiz();
    } catch (err) {
      console.error("Failed to reorder questions:", err);
    }
  };

  // Handle Publish
  const handlePublish = async () => {
    if (!quiz.questions || quiz.questions.length === 0) {
      alert("Please add at least one question before publishing.");
      return;
    }
    if (
      !window.confirm(
        "Publish this quiz? Enrolled students will immediately be able to view and take it."
      )
    )
      return;

    try {
      setActionLoading(true);
      await facultyApi.publishQuiz(quizId);
      setSuccessMsg("Quiz published successfully! Students can now take it.");
      setTimeout(() => setSuccessMsg(""), 4000);
      fetchQuiz();
    } catch (err) {
      alert(err?.response?.data?.detail || "Failed to publish quiz");
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Archive
  const handleArchive = async () => {
    if (!window.confirm("Archive this quiz? It will no longer accept student submissions."))
      return;
    try {
      setActionLoading(true);
      await facultyApi.archiveQuiz(quizId);
      fetchQuiz();
    } catch (err) {
      alert(err?.response?.data?.detail || "Failed to archive quiz");
    } finally {
      setActionLoading(false);
    }
  };

  const statusStyles = {
    draft: "bg-amber-50 text-amber-700 border-amber-200",
    published: "bg-emerald-50 text-emerald-700 border-emerald-200",
    archived: "bg-rose-50 text-rose-700 border-rose-200",
  };

  const questions = quiz?.questions || [];

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-16 animate-fadeIn">
      {/* Top Bar Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab("quizzes")}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-white rounded-xl border border-gray-200 transition"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border ${
                  statusStyles[quiz?.status] || statusStyles.draft
                }`}
              >
                {quiz?.status || "Draft"}
              </span>
              <h2 className="text-xl font-bold text-gray-900">{quiz?.title}</h2>
            </div>
            <p className="text-xs text-gray-500 mt-0.5">
              Course: <strong className="text-gray-700">{quiz?.course?.title || "Assigned Course"}</strong> • {questions.length} questions
            </p>
          </div>
        </div>

        {/* Global Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => setIsPreviewOpen(true)}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 border border-gray-200 rounded-xl shadow-sm transition"
          >
            <Eye className="w-4 h-4 text-gray-500" />
            Preview
          </button>

          {quiz?.status === "published" && (
            <button
              onClick={() => {
                if (setViewingQuizId) setViewingQuizId(quizId);
                setActiveTab("quiz-submissions");
              }}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-xl transition"
            >
              <Users className="w-4 h-4 text-blue-600" />
              Submissions
            </button>
          )}

          {quiz?.status === "draft" ? (
            <button
              onClick={handlePublish}
              disabled={actionLoading || questions.length === 0}
              className="flex items-center gap-1.5 px-5 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 rounded-xl shadow-md shadow-emerald-600/20 transition"
            >
              <Send className="w-4 h-4" />
              Publish Quiz
            </button>
          ) : quiz?.status === "published" ? (
            <button
              onClick={handleArchive}
              disabled={actionLoading}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-xl transition"
            >
              <Archive className="w-4 h-4" />
              Archive
            </button>
          ) : null}
        </div>
      </div>

      {/* Messages */}
      {successMsg && (
        <div className="flex items-center gap-2 p-4 text-sm text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-2xl animate-fadeIn">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-600" />
          <span>{successMsg}</span>
        </div>
      )}
      {error && (
        <div className="flex items-center gap-2 p-4 text-sm text-red-800 bg-red-50 border border-red-200 rounded-2xl">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Metadata Configuration Card */}
      <div className="p-6 rounded-3xl bg-white border border-gray-100 shadow-sm space-y-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500">Quiz Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2 space-y-3">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Quiz Title *</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3.5 py-2 text-sm rounded-xl border border-gray-200 focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Instructions / Description</label>
              <textarea
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional instructions for students..."
                className="w-full px-3.5 py-2 text-sm rounded-xl border border-gray-200 focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Passing Score (%)</label>
              <input
                type="number"
                min={0}
                max={100}
                value={passingScore}
                onChange={(e) => setPassingScore(e.target.value)}
                className="w-full px-3.5 py-2 text-sm rounded-xl border border-gray-200 focus:ring-2 focus:ring-emerald-500"
              />
              <p className="text-[11px] text-gray-400 mt-1">Minimum score required to earn credit</p>
            </div>

            <div className="pt-3">
              <button
                onClick={handleSaveMetadata}
                disabled={savingMeta}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-xl transition"
              >
                <Save className="w-4 h-4" />
                {savingMeta ? "Saving..." : "Save Settings"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Questions Section Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
        <div>
          <h3 className="text-base font-bold text-gray-900">
            Questions ({questions.length})
          </h3>
          <p className="text-xs text-gray-500">
            Click edit to adjust questions, change correct options, or write explanations
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setIsAiModalOpen(true)}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 border border-teal-200 rounded-xl transition"
          >
            <Sparkles className="w-4 h-4 text-teal-600" />
            AI Generate More
          </button>
          <button
            onClick={() => {
              setEditingQuestion(null);
              setIsQuestionEditorOpen(true);
            }}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-sm transition"
          >
            <Plus className="w-4 h-4" />
            Add Question
          </button>
        </div>
      </div>

      {/* Questions List */}
      {questions.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-3xl border border-gray-100 shadow-sm">
          <HelpCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h4 className="text-sm font-bold text-gray-700">No questions added yet</h4>
          <p className="text-xs text-gray-400 mt-1 mb-5 max-w-sm mx-auto">
            Get started by adding questions manually or click "AI Generate More" to auto-generate them from your course documents!
          </p>
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={() => setIsAiModalOpen(true)}
              className="flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-xl shadow-md transition"
            >
              <Sparkles className="w-4 h-4 text-amber-200" />
              Generate with AI
            </button>
            <button
              onClick={() => {
                setEditingQuestion(null);
                setIsQuestionEditorOpen(true);
              }}
              className="px-5 py-2.5 text-xs font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition"
            >
              Add Manually
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {questions.map((q, idx) => (
            <div
              key={q.id}
              className="p-6 rounded-3xl bg-white border border-gray-100 shadow-sm hover:border-gray-200 transition-all space-y-4 group"
            >
              {/* Question Top Row */}
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <span className="w-7 h-7 rounded-xl bg-gray-100 text-gray-700 text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 leading-relaxed">
                      {q.questionText}
                    </h4>
                    <span className="text-[11px] text-gray-400 font-medium">
                      {q.points || 1} point{q.points > 1 ? "s" : ""}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1 flex-shrink-0">
                  <button
                    onClick={() => handleMoveQuestion(idx, "up")}
                    disabled={idx === 0}
                    title="Move question up"
                    className="p-1.5 text-gray-400 hover:text-gray-700 disabled:opacity-20 rounded-lg hover:bg-gray-100"
                  >
                    <ChevronUp className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleMoveQuestion(idx, "down")}
                    disabled={idx === questions.length - 1}
                    title="Move question down"
                    className="p-1.5 text-gray-400 hover:text-gray-700 disabled:opacity-20 rounded-lg hover:bg-gray-100"
                  >
                    <ChevronDown className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => {
                      setEditingQuestion(q);
                      setIsQuestionEditorOpen(true);
                    }}
                    title="Edit question"
                    className="p-1.5 text-gray-500 hover:text-emerald-700 rounded-lg hover:bg-emerald-50"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteQuestion(q.id)}
                    title="Delete question"
                    className="p-1.5 text-gray-400 hover:text-rose-600 rounded-lg hover:bg-rose-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Options Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pl-10">
                {q.options?.map((opt, oIdx) => {
                  const isCorrect = opt === q.correctAnswer;
                  const optionLetters = ["A", "B", "C", "D"];
                  return (
                    <div
                      key={oIdx}
                      className={`p-3 rounded-2xl border text-xs flex items-center justify-between gap-2 transition ${
                        isCorrect
                          ? "border-emerald-300 bg-emerald-50/50 text-emerald-900 font-semibold ring-1 ring-emerald-300"
                          : "border-gray-100 bg-gray-50/50 text-gray-600"
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <span
                          className={`w-5 h-5 rounded-lg flex items-center justify-center font-bold text-[10px] ${
                            isCorrect ? "bg-emerald-600 text-white" : "bg-gray-200 text-gray-600"
                          }`}
                        >
                          {optionLetters[oIdx] || oIdx + 1}
                        </span>
                        <span className="truncate">{opt}</span>
                      </div>
                      {isCorrect && (
                        <span className="flex items-center gap-1 text-[10px] text-emerald-700 font-bold uppercase tracking-wider bg-emerald-100/80 px-2 py-0.5 rounded-full flex-shrink-0">
                          <CheckCircle2 className="w-3 h-3" /> Correct
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Explanation Box */}
              {q.explanation && (
                <div className="ml-10 p-3 rounded-2xl bg-teal-50/40 border border-teal-100 text-xs text-teal-900">
                  <strong className="text-teal-950">Explanation:</strong> {q.explanation}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Question Editor Modal */}
      <QuestionEditor
        isOpen={isQuestionEditorOpen}
        onClose={() => {
          setIsQuestionEditorOpen(false);
          setEditingQuestion(null);
        }}
        onSave={handleSaveQuestion}
        question={editingQuestion}
        totalQuestions={questions.length}
      />

      {/* AI Generator Modal */}
      <QuizAIGenerator
        isOpen={isAiModalOpen}
        onClose={() => setIsAiModalOpen(false)}
        onSuccess={() => {
          fetchQuiz();
          setSuccessMsg("AI questions successfully generated and added!");
          setTimeout(() => setSuccessMsg(""), 3000);
        }}
        initialCourseId={quiz?.courseId}
        courses={quiz?.course ? [quiz.course] : []}
      />
    </div>
  );
}

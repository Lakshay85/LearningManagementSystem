import { useState, useEffect } from "react";
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  ChevronRight,
  ChevronLeft,
  Send,
  Award,
  BookOpen,
  ArrowLeft,
  Sparkles,
  HelpCircle,
  Loader2
} from "lucide-react";
import studentApi from "../../utils/studentApi";

export default function Quiz({ quizId, onComplete, onBack }) {
  const [quiz, setQuiz] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  // Fetch quiz for taking
  useEffect(() => {
    if (!quizId) {
      setLoading(false);
      return;
    }

    const fetchQuiz = async () => {
      try {
        setLoading(true);
        setError("");
        const res = await studentApi.getQuizForTaking(quizId);
        const data = res?.data || res;
        setQuiz(data);

        // If already submitted, show results view directly
        if (data.hasSubmitted && data.submission) {
          setSubmissionResult(data.submission);
        }
      } catch (err) {
        console.error("Error loading quiz:", err);
        setError(
          err?.response?.data?.detail || "Failed to load quiz. Please verify course enrollment."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchQuiz();
  }, [quizId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
        <Loader2 className="w-8 h-8 text-emerald-600 animate-spin mb-3" />
        <p className="text-sm font-medium text-gray-500">Loading quiz questions...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-xl mx-auto p-8 bg-white rounded-3xl border border-gray-100 shadow-sm text-center my-8">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto mb-3" />
        <h3 className="text-base font-bold text-gray-900 mb-1">Cannot Load Quiz</h3>
        <p className="text-xs text-gray-500 mb-4">{error}</p>
        {onBack && (
          <button
            onClick={onBack}
            className="px-5 py-2 text-xs font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition"
          >
            Go Back
          </button>
        )}
      </div>
    );
  }

  if (!quiz) {
    return (
      <div className="max-w-xl mx-auto p-8 bg-white rounded-3xl border border-gray-100 shadow-sm text-center my-8">
        <HelpCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
        <h3 className="text-base font-bold text-gray-800">No Quiz Selected</h3>
        <p className="text-xs text-gray-500 mt-1">Please select a quiz from your course to begin.</p>
      </div>
    );
  }

  const questions = quiz.questions || [];
  const currentQ = questions[currentQuestionIndex];
  const answeredCount = Object.keys(selectedAnswers).length;
  const progressPercent = Math.round((answeredCount / Math.max(1, questions.length)) * 100);

  const handleSelectOption = (questionId, option) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: option,
    }));
  };

  const handleSubmit = async () => {
    try {
      setSubmitting(true);
      setError("");

      const formattedAnswers = Object.entries(selectedAnswers).map(
        ([questionId, selectedAnswer]) => ({
          questionId,
          selectedAnswer,
        })
      );

      const res = await studentApi.submitQuiz(quizId, formattedAnswers);
      const resultData = res?.data || res;
      setSubmissionResult(resultData);
      setShowConfirmModal(false);
      if (onComplete) onComplete(resultData);
    } catch (err) {
      console.error("Submission failed:", err);
      setError(err?.response?.data?.detail || "Submission failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  // ==================== RESULTS VIEW ====================
  if (submissionResult) {
    const isPassed =
      quiz.passingScore != null
        ? Number(submissionResult.score) >= quiz.passingScore
        : Number(submissionResult.score) >= 60;

    return (
      <div className="max-w-3xl mx-auto space-y-6 animate-fadeIn py-6">
        {/* Results Banner */}
        <div
          className={`p-8 rounded-3xl border text-center relative overflow-hidden shadow-sm ${
            isPassed
              ? "bg-gradient-to-b from-emerald-50 to-white border-emerald-200"
              : "bg-gradient-to-b from-rose-50 to-white border-rose-200"
          }`}
        >
          <div
            className={`w-16 h-16 rounded-3xl flex items-center justify-center mx-auto mb-3 shadow-md ${
              isPassed ? "bg-emerald-600 text-white" : "bg-rose-500 text-white"
            }`}
          >
            {isPassed ? <Award className="w-8 h-8" /> : <AlertCircle className="w-8 h-8" />}
          </div>

          <h2 className="text-2xl font-black text-gray-900">
            {isPassed ? "Congratulations! You Passed!" : "Quiz Completed"}
          </h2>
          <p className="text-xs text-gray-500 mt-1">
            {quiz.title} • Submitted on{" "}
            {submissionResult.submittedAt
              ? new Date(submissionResult.submittedAt).toLocaleDateString()
              : "Recently"}
          </p>

          <div className="inline-flex items-center justify-center gap-8 mt-6 p-4 px-8 rounded-2xl bg-white border border-gray-100 shadow-sm">
            <div>
              <span className="block text-3xl font-black text-emerald-600">
                {submissionResult.score}%
              </span>
              <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400">
                Your Score
              </span>
            </div>
            <div className="h-10 w-px bg-gray-100" />
            <div>
              <span className="block text-3xl font-black text-gray-900">
                {submissionResult.totalCorrect} / {submissionResult.totalQuestions}
              </span>
              <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400">
                Correct Answers
              </span>
            </div>
            {quiz.passingScore && (
              <>
                <div className="h-10 w-px bg-gray-100" />
                <div>
                  <span className="block text-3xl font-black text-gray-700">
                    {quiz.passingScore}%
                  </span>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400">
                    Required Pass
                  </span>
                </div>
              </>
            )}
          </div>

          {onBack && (
            <div className="mt-6">
              <button
                onClick={onBack}
                className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 border border-gray-200 rounded-xl shadow-sm transition"
              >
                <ArrowLeft className="w-4 h-4" />
                Return to Course
              </button>
            </div>
          )}
        </div>

        {/* Detailed Question Review List */}
        {submissionResult.answers && submissionResult.answers.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500 px-1">
              Detailed Question Review
            </h3>

            {submissionResult.answers.map((ans, idx) => (
              <div
                key={idx}
                className={`p-6 rounded-3xl bg-white border shadow-sm space-y-3 transition ${
                  ans.isCorrect ? "border-emerald-200" : "border-rose-200"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <span className="text-xs font-bold text-gray-400">Question {idx + 1}</span>
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold ${
                      ans.isCorrect
                        ? "bg-emerald-100 text-emerald-800"
                        : "bg-rose-100 text-rose-800"
                    }`}
                  >
                    {ans.isCorrect ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5" /> Correct
                      </>
                    ) : (
                      <>
                        <XCircle className="w-3.5 h-3.5" /> Incorrect
                      </>
                    )}
                  </span>
                </div>

                <h4 className="text-sm font-semibold text-gray-900">{ans.questionText}</h4>

                <div className="space-y-1.5 text-xs pt-1">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 w-28 font-medium">Your Answer:</span>
                    <span
                      className={`font-bold ${
                        ans.isCorrect ? "text-emerald-700" : "text-rose-700"
                      }`}
                    >
                      {ans.selectedAnswer || "(No answer selected)"}
                    </span>
                  </div>

                  {!ans.isCorrect && (
                    <div className="flex items-center gap-2">
                      <span className="text-gray-500 w-28 font-medium">Correct Key:</span>
                      <span className="font-bold text-emerald-700">{ans.correctAnswer}</span>
                    </div>
                  )}

                  {ans.explanation && (
                    <div className="mt-3 p-3.5 rounded-2xl bg-teal-50/50 border border-teal-100 text-teal-900 text-xs">
                      <strong className="text-teal-950">Why:</strong> {ans.explanation}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ==================== TAKING QUIZ VIEW ====================
  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fadeIn py-6 pb-16">
      {/* Quiz Header Card */}
      <div className="p-6 rounded-3xl bg-white border border-gray-100 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-100">
                Single Attempt Only
              </span>
              {quiz.passingScore && (
                <span className="text-xs text-gray-500 font-medium">
                  Passing score: {quiz.passingScore}%
                </span>
              )}
            </div>
            <h2 className="text-xl font-bold text-gray-900 mt-2">{quiz.title}</h2>
            {quiz.description && (
              <p className="text-xs text-gray-500 mt-1 max-w-xl">{quiz.description}</p>
            )}
          </div>

          <div className="flex items-center gap-3">
            {onBack && (
              <button
                onClick={onBack}
                className="px-3 py-1.5 text-xs font-semibold text-gray-600 hover:text-gray-900 bg-gray-50 hover:bg-gray-100 rounded-xl transition"
              >
                Back
              </button>
            )}
            <button
              onClick={() => setShowConfirmModal(true)}
              disabled={answeredCount === 0}
              className="flex items-center gap-1.5 px-5 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 rounded-xl shadow-md shadow-emerald-600/20 transition"
            >
              <Send className="w-3.5 h-3.5" /> Submit Quiz
            </button>
          </div>
        </div>

        {/* Progress Bar & Answered Indicator */}
        <div className="space-y-1.5 pt-2 border-t border-gray-100">
          <div className="flex justify-between text-xs font-semibold text-gray-600">
            <span>
              Question {currentQuestionIndex + 1} of {questions.length}
            </span>
            <span className="text-emerald-700 font-bold">
              {answeredCount} of {questions.length} Answered ({progressPercent}%)
            </span>
          </div>
          <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-emerald-600 rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-2xl">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Question Card */}
      {currentQ && (
        <div className="p-8 rounded-3xl bg-white border border-gray-100 shadow-sm space-y-6">
          {/* Question Dots Navigation */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-2 border-b border-gray-100">
            {questions.map((q, idx) => {
              const isAnswered = selectedAnswers[q.id] !== undefined;
              const isCurrent = currentQuestionIndex === idx;
              return (
                <button
                  key={q.id}
                  onClick={() => setCurrentQuestionIndex(idx)}
                  className={`w-7 h-7 rounded-lg text-xs font-bold transition-all ${
                    isCurrent
                      ? "bg-emerald-600 text-white ring-2 ring-emerald-600/30 scale-105"
                      : isAnswered
                      ? "bg-emerald-100 text-emerald-800"
                      : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                  }`}
                >
                  {idx + 1}
                </button>
              );
            })}
          </div>

          <h3 className="text-lg font-semibold text-gray-900 leading-relaxed">
            {currentQ.questionText}
          </h3>

          {/* Options */}
          <div className="space-y-3">
            {currentQ.options?.map((opt, idx) => {
              const isSelected = selectedAnswers[currentQ.id] === opt;
              const optionLetters = ["A", "B", "C", "D"];
              return (
                <button
                  key={idx}
                  onClick={() => handleSelectOption(currentQ.id, opt)}
                  className={`w-full p-4 rounded-2xl border text-left flex items-center gap-4 transition-all ${
                    isSelected
                      ? "border-emerald-600 bg-emerald-50/60 ring-2 ring-emerald-600/20 shadow-sm"
                      : "border-gray-200 hover:border-gray-300 hover:bg-gray-50/50 bg-white"
                  }`}
                >
                  <span
                    className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold flex-shrink-0 transition-colors ${
                      isSelected
                        ? "bg-emerald-600 text-white shadow-sm"
                        : "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {optionLetters[idx] || idx + 1}
                  </span>
                  <span className="text-sm font-medium text-gray-800 flex-1">{opt}</span>
                  {isSelected && <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />}
                </button>
              );
            })}
          </div>

          {/* Nav Buttons */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-100">
            <button
              onClick={() => setCurrentQuestionIndex((prev) => Math.max(0, prev - 1))}
              disabled={currentQuestionIndex === 0}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-gray-600 hover:text-gray-900 disabled:opacity-30 transition"
            >
              <ChevronLeft className="w-4 h-4" /> Previous
            </button>

            {currentQuestionIndex < questions.length - 1 ? (
              <button
                onClick={() =>
                  setCurrentQuestionIndex((prev) => Math.min(questions.length - 1, prev + 1))
                }
                className="flex items-center gap-1.5 px-5 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl transition shadow-sm"
              >
                Next <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={() => setShowConfirmModal(true)}
                className="flex items-center gap-1.5 px-6 py-2 text-xs font-bold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-xl shadow-md transition"
              >
                Review & Submit <Send className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Confirmation Submit Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white rounded-3xl shadow-2xl border border-gray-100 max-w-md w-full p-6 space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold mx-auto">
              <Send className="w-6 h-6" />
            </div>

            <div className="text-center">
              <h3 className="text-lg font-bold text-gray-900">Submit Quiz Responses?</h3>
              <p className="text-xs text-gray-500 mt-1">
                You have answered <strong className="text-emerald-700">{answeredCount}</strong> of{" "}
                <strong className="text-gray-900">{questions.length}</strong> questions.
              </p>
              <p className="text-xs text-rose-600 font-medium mt-2 bg-rose-50 p-2 rounded-xl">
                ⚠️ You can only submit your response ONCE. No retakes are allowed.
              </p>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowConfirmModal(false)}
                disabled={submitting}
                className="flex-1 py-2.5 text-xs font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition"
              >
                Keep Reviewing
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={submitting}
                className="flex-1 py-2.5 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-md transition disabled:opacity-50 flex items-center justify-center gap-1.5"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" /> Submitting...
                  </>
                ) : (
                  "Confirm Submit"
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

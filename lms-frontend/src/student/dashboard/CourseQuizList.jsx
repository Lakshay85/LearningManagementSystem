import { useState, useEffect } from "react";
import {
  ClipboardCheck,
  CheckCircle2,
  Clock,
  ArrowRight,
  HelpCircle,
  AlertCircle,
  Eye,
  Loader2
} from "lucide-react";
import studentApi from "../../utils/studentApi";
import Quiz from "./Quiz";

export default function CourseQuizList({ courseId, courseTitle }) {
  const [quizzes, setQuizzes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeQuizId, setActiveQuizId] = useState(null);

  const fetchQuizzes = async () => {
    if (!courseId) return;
    try {
      setLoading(true);
      setError("");
      const res = await studentApi.getCourseQuizzes(courseId);
      setQuizzes(res?.data || res || []);
    } catch (err) {
      console.error("Error loading course quizzes:", err);
      setError("Failed to load quizzes for this course.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuizzes();
  }, [courseId]);

  // If a quiz is active, render the Quiz component
  if (activeQuizId) {
    return (
      <Quiz
        quizId={activeQuizId}
        onBack={() => {
          setActiveQuizId(null);
          fetchQuizzes();
        }}
        onComplete={() => fetchQuizzes()}
      />
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12">
        <Loader2 className="w-8 h-8 text-emerald-600 animate-spin mb-3" />
        <p className="text-xs font-medium text-gray-500">Loading course quizzes...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-fadeIn p-4">
      <div className="flex items-center justify-between pb-3 border-b border-gray-100">
        <div>
          <h3 className="text-base font-bold text-gray-900">Course Quizzes & Assessments</h3>
          <p className="text-xs text-gray-500">
            Complete quizzes to test your understanding of {courseTitle || "the course"}
          </p>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700">
          {quizzes.length} Quizzes
        </span>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 text-xs text-red-700 bg-red-50 border border-red-200 rounded-xl">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {quizzes.length === 0 ? (
        <div className="p-12 text-center bg-gray-50/60 rounded-3xl border border-gray-100">
          <HelpCircle className="w-10 h-10 text-gray-300 mx-auto mb-2" />
          <h4 className="text-sm font-bold text-gray-700">No quizzes available</h4>
          <p className="text-xs text-gray-400 mt-1 max-w-sm mx-auto">
            The instructor has not published any quizzes for this course yet.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {quizzes.map((q) => {
            const hasSubmitted = q.hasSubmitted;
            return (
              <div
                key={q.id}
                className="p-5 rounded-3xl bg-white border border-gray-100 shadow-sm hover:shadow-md hover:border-gray-200 transition-all flex flex-col justify-between space-y-4"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full ${
                        hasSubmitted
                          ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                          : "bg-blue-50 text-blue-700 border border-blue-200"
                      }`}
                    >
                      {hasSubmitted ? (
                        <>
                          <CheckCircle2 className="w-3 h-3" /> Completed: {q.score}%
                        </>
                      ) : (
                        "Not Attempted"
                      )}
                    </span>
                    <span className="text-[11px] font-medium text-gray-400">
                      {q.totalQuestions || 0} Questions
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-gray-900 line-clamp-1">{q.title}</h4>
                  {q.description && (
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">{q.description}</p>
                  )}
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-gray-50 text-xs">
                  <span className="text-gray-400">
                    Passing: <strong className="text-gray-600">{q.passingScore || 60}%</strong>
                  </span>

                  <button
                    onClick={() => setActiveQuizId(q.id)}
                    className={`inline-flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-xs font-bold transition shadow-sm ${
                      hasSubmitted
                        ? "bg-gray-100 hover:bg-gray-200 text-gray-700"
                        : "bg-emerald-600 hover:bg-emerald-700 text-white"
                    }`}
                  >
                    {hasSubmitted ? (
                      <>
                        <Eye className="w-3.5 h-3.5" /> View Result
                      </>
                    ) : (
                      <>
                        Take Quiz <ArrowRight className="w-3.5 h-3.5" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

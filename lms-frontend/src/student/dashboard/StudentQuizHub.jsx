import { useState, useEffect } from "react";
import {
  HelpCircle,
  ClipboardCheck,
  CheckCircle2,
  BookOpen,
  ArrowRight,
  Eye,
  AlertCircle,
  Loader2
} from "lucide-react";
import studentApi from "../../utils/studentApi";
import Quiz from "./Quiz";

export default function StudentQuizHub() {
  const [enrolledCourses, setEnrolledCourses] = useState([]);
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [quizzes, setQuizzes] = useState([]);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [loadingQuizzes, setLoadingQuizzes] = useState(false);
  const [error, setError] = useState("");
  const [activeQuizId, setActiveQuizId] = useState(null);

  // 1. Fetch student's enrolled courses
  useEffect(() => {
    const fetchEnrolled = async () => {
      try {
        setLoadingCourses(true);
        const res = await studentApi.getMyEnrolledCourses();
        const enrollments = res?.data || res || [];
        const courses = enrollments
          .map((e) => e.course || e)
          .filter((c) => c && c.id);

        setEnrolledCourses(courses);
        if (courses.length > 0) {
          setSelectedCourseId(courses[0].id);
        }
      } catch (err) {
        console.error("Failed to load enrolled courses:", err);
        setError("Failed to load your enrolled courses.");
      } finally {
        setLoadingCourses(false);
      }
    };
    fetchEnrolled();
  }, []);

  // 2. Fetch quizzes for selected course
  const fetchQuizzes = async (courseId) => {
    if (!courseId) return;
    try {
      setLoadingQuizzes(true);
      setError("");
      const res = await studentApi.getCourseQuizzes(courseId);
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

  // If a quiz is being taken or viewed, render Quiz component
  if (activeQuizId) {
    return (
      <Quiz
        quizId={activeQuizId}
        onBack={() => {
          setActiveQuizId(null);
          fetchQuizzes(selectedCourseId);
        }}
        onComplete={() => {
          fetchQuizzes(selectedCourseId);
        }}
      />
    );
  }

  if (loadingCourses) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[350px]">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mb-3" />
        <p className="text-xs text-gray-500 font-medium">Loading your enrolled courses...</p>
      </div>
    );
  }

  const selectedCourse = enrolledCourses.find((c) => c.id === selectedCourseId);

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fadeIn pb-16">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black tracking-tight text-gray-900">
          Quizzes & Knowledge Checks
        </h1>
        <p className="text-xs text-gray-500 mt-1">
          Take assessments created by your faculty to test your mastery. Each quiz can be submitted once.
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3.5 text-xs text-red-700 bg-red-50 border border-red-200 rounded-2xl">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {enrolledCourses.length === 0 ? (
        <div className="p-16 text-center bg-white rounded-3xl border border-gray-100 shadow-sm">
          <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-gray-800">No Enrolled Courses Found</h3>
          <p className="text-xs text-gray-400 mt-1 max-w-sm mx-auto">
            Enroll in courses to access course-specific quizzes and AI assessments.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Course Tabs / Selection */}
          <div className="p-5 rounded-3xl bg-white border border-gray-100 shadow-sm flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-2 overflow-x-auto max-w-full pb-1">
              {enrolledCourses.map((c) => {
                const isSelected = c.id === selectedCourseId;
                return (
                  <button
                    key={c.id}
                    onClick={() => setSelectedCourseId(c.id)}
                    className={`px-4 py-2 rounded-2xl text-xs font-semibold whitespace-nowrap transition-all ${
                      isSelected
                        ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                        : "bg-gray-50 text-gray-600 hover:bg-gray-100"
                    }`}
                  >
                    {c.title}
                  </button>
                );
              })}
            </div>

            <span className="text-xs font-medium text-gray-400">
              {quizzes.length} Quizzes in this Course
            </span>
          </div>

          {/* Quizzes List */}
          {loadingQuizzes ? (
            <div className="flex flex-col items-center justify-center min-h-[250px]">
              <Loader2 className="w-7 h-7 text-indigo-600 animate-spin mb-2" />
              <p className="text-xs text-gray-400">Loading quizzes...</p>
            </div>
          ) : quizzes.length === 0 ? (
            <div className="p-16 text-center bg-white rounded-3xl border border-gray-100 shadow-sm">
              <HelpCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-gray-700">No Quizzes Published Yet</h3>
              <p className="text-xs text-gray-400 mt-1 max-w-sm mx-auto">
                Your instructor has not yet published any quizzes for{" "}
                <strong className="text-gray-600">{selectedCourse?.title}</strong>. Check back soon!
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {quizzes.map((q) => {
                const hasSubmitted = q.hasSubmitted;
                return (
                  <div
                    key={q.id}
                    className="p-6 rounded-3xl bg-white border border-gray-100 shadow-sm hover:shadow-md hover:border-gray-200 transition-all flex flex-col justify-between space-y-4"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span
                          className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full ${
                            hasSubmitted
                              ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                              : "bg-indigo-50 text-indigo-700 border border-indigo-200"
                          }`}
                        >
                          {hasSubmitted ? (
                            <>
                              <CheckCircle2 className="w-3.5 h-3.5" /> Completed: {q.score}%
                            </>
                          ) : (
                            "Not Attempted"
                          )}
                        </span>
                        <span className="text-xs text-gray-400 font-medium">
                          {q.totalQuestions || 0} Questions
                        </span>
                      </div>

                      <h3 className="text-base font-bold text-gray-900 line-clamp-1">{q.title}</h3>
                      <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                        {q.description || "Course assessment to test knowledge retention."}
                      </p>
                    </div>

                    <div className="flex items-center justify-between pt-4 border-t border-gray-100 text-xs">
                      <span className="text-gray-400">
                        Pass Mark:{" "}
                        <strong className="text-gray-700">{q.passingScore || 60}%</strong>
                      </span>

                      <button
                        onClick={() => setActiveQuizId(q.id)}
                        className={`inline-flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-bold transition shadow-sm ${
                          hasSubmitted
                            ? "bg-gray-100 hover:bg-gray-200 text-gray-800"
                            : "bg-indigo-600 hover:bg-indigo-700 text-white shadow-indigo-600/20"
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
      )}
    </div>
  );
}

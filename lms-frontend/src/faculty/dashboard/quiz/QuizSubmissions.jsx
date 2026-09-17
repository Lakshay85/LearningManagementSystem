import { useState, useEffect } from "react";
import {
  ArrowLeft,
  Users,
  CheckCircle2,
  XCircle,
  Clock,
  Eye,
  X,
  Award,
  BarChart2,
  AlertCircle,
  FileSpreadsheet,
  Loader2
} from "lucide-react";
import facultyApi from "../../../utils/facultyApi";

export default function QuizSubmissions({ quizId, setActiveTab }) {
  const [quiz, setQuiz] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedSubmission, setSelectedSubmission] = useState(null);

  useEffect(() => {
    if (!quizId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError("");
        const [quizRes, subRes] = await Promise.all([
          facultyApi.getQuiz(quizId),
          facultyApi.getQuizSubmissions(quizId),
        ]);
        setQuiz(quizRes?.data || quizRes);
        setSubmissions(subRes?.data || subRes || []);
      } catch (err) {
        console.error("Error loading submissions:", err);
        setError("Failed to load submissions for this quiz.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [quizId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 text-emerald-600 animate-spin mb-3" />
        <p className="text-sm text-gray-500 font-medium">Loading submissions data...</p>
      </div>
    );
  }

  // Calculate statistics
  const totalSubmissions = submissions.length;
  const avgScore =
    totalSubmissions > 0
      ? Math.round(
          submissions.reduce((acc, curr) => acc + Number(curr.score), 0) /
            totalSubmissions
        )
      : 0;

  const passingScore = quiz?.passingScore || 60;
  const passedCount = submissions.filter((s) => Number(s.score) >= passingScore).length;
  const passRate =
    totalSubmissions > 0 ? Math.round((passedCount / totalSubmissions) * 100) : 0;

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12 animate-fadeIn">
      {/* Top Navigation */}
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
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-100">
                {quiz?.status || "Published"}
              </span>
              <h2 className="text-xl font-bold text-gray-900">{quiz?.title} — Submissions</h2>
            </div>
            <p className="text-xs text-gray-500 mt-0.5">
              Review student scores, response analytics, and individual answers
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-2xl">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="p-6 rounded-3xl bg-white border border-gray-100 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Total Attempts</span>
            <div className="text-2xl font-black text-gray-900 mt-0.5">{totalSubmissions}</div>
          </div>
        </div>

        <div className="p-6 rounded-3xl bg-white border border-gray-100 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
            <BarChart2 className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Average Score</span>
            <div className="text-2xl font-black text-emerald-600 mt-0.5">{avgScore}%</div>
          </div>
        </div>

        <div className="p-6 rounded-3xl bg-white border border-gray-100 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-gray-400">
              Pass Rate ({passingScore}% threshold)
            </span>
            <div className="text-2xl font-black text-purple-600 mt-0.5">{passRate}%</div>
          </div>
        </div>
      </div>

      {/* Submissions Table */}
      <div className="bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 className="text-sm font-bold text-gray-900">Student Responses ({totalSubmissions})</h3>
        </div>

        {submissions.length === 0 ? (
          <div className="p-12 text-center">
            <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <h4 className="text-sm font-bold text-gray-700">No submissions yet</h4>
            <p className="text-xs text-gray-400 mt-1 max-w-sm mx-auto">
              Once enrolled students complete this quiz, their scores and answer breakdowns will appear here.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50/75 border-b border-gray-100 text-[11px] font-bold uppercase tracking-wider text-gray-500">
                <tr>
                  <th className="px-6 py-3">Student</th>
                  <th className="px-6 py-3">Score</th>
                  <th className="px-6 py-3">Correct Answers</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Submitted At</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {submissions.map((sub) => {
                  const isPass = Number(sub.score) >= passingScore;
                  return (
                    <tr key={sub.id} className="hover:bg-gray-50/60 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold text-xs">
                            {sub.studentName?.[0] || "S"}
                          </div>
                          <div>
                            <div className="font-semibold text-gray-900">{sub.studentName}</div>
                            <div className="text-xs text-gray-400">{sub.studentEmail}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-extrabold text-base text-gray-900">{sub.score}%</span>
                      </td>
                      <td className="px-6 py-4 text-xs font-medium text-gray-600">
                        {sub.totalCorrect} / {sub.totalQuestions}
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
                            isPass
                              ? "bg-emerald-100 text-emerald-800"
                              : "bg-rose-100 text-rose-800"
                          }`}
                        >
                          {isPass ? (
                            <>
                              <CheckCircle2 className="w-3 h-3" /> Passed
                            </>
                          ) : (
                            <>
                              <XCircle className="w-3 h-3" /> Failed
                            </>
                          )}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-xs text-gray-500">
                        {sub.submittedAt ? new Date(sub.submittedAt).toLocaleString() : "—"}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => setSelectedSubmission(sub)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-emerald-700 hover:text-emerald-800 bg-emerald-50 hover:bg-emerald-100 rounded-xl transition"
                        >
                          <Eye className="w-3.5 h-3.5" /> View Answers
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Answer Detail Modal */}
      {selectedSubmission && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white rounded-3xl shadow-2xl border border-gray-100 max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50/75">
              <div>
                <h3 className="text-base font-bold text-gray-900">
                  {selectedSubmission.studentName}'s Responses
                </h3>
                <p className="text-xs text-gray-500">
                  Score: <strong className="text-emerald-700">{selectedSubmission.score}%</strong> (
                  {selectedSubmission.totalCorrect} / {selectedSubmission.totalQuestions} correct)
                </p>
              </div>
              <button
                onClick={() => setSelectedSubmission(null)}
                className="p-1.5 text-gray-400 hover:text-gray-600 rounded-xl hover:bg-gray-100 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {selectedSubmission.answers?.map((ans, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-2xl border transition-all ${
                    ans.isCorrect
                      ? "border-emerald-200 bg-emerald-50/30"
                      : "border-rose-200 bg-rose-50/30"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-gray-500">
                      Question {idx + 1}
                    </span>
                    <span
                      className={`inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full ${
                        ans.isCorrect
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-rose-100 text-rose-800"
                      }`}
                    >
                      {ans.isCorrect ? (
                        <>
                          <CheckCircle2 className="w-3 h-3" /> Correct
                        </>
                      ) : (
                        <>
                          <XCircle className="w-3 h-3" /> Incorrect
                        </>
                      )}
                    </span>
                  </div>

                  <h4 className="text-sm font-semibold text-gray-900 mb-3">{ans.questionText}</h4>

                  <div className="space-y-1.5 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-500 w-24">Student Choice:</span>
                      <span
                        className={`font-bold ${
                          ans.isCorrect ? "text-emerald-700" : "text-rose-700"
                        }`}
                      >
                        {ans.selectedAnswer || "(No answer chosen)"}
                      </span>
                    </div>

                    {!ans.isCorrect && (
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-500 w-24">Correct Key:</span>
                        <span className="font-bold text-emerald-700">{ans.correctAnswer}</span>
                      </div>
                    )}

                    {ans.explanation && (
                      <div className="mt-2 pt-2 border-t border-gray-100 text-gray-600">
                        <strong className="text-gray-700">Explanation:</strong> {ans.explanation}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-gray-100 bg-gray-50/50 flex justify-end">
              <button
                onClick={() => setSelectedSubmission(null)}
                className="px-5 py-2 text-xs font-semibold text-gray-700 bg-white hover:bg-gray-100 border border-gray-200 rounded-xl transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

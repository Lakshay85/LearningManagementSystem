import { useState } from "react";
import {
  ArrowLeft,
  CheckCircle2,
  HelpCircle,
  Eye,
  ChevronRight,
  ChevronLeft,
  RotateCcw,
  Sparkles
} from "lucide-react";

export default function QuizPreview({ quiz, onBack }) {
  const questions = quiz?.questions || [];
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);

  const currentQ = questions[currentIndex];

  const handleSelectOption = (questionId, option) => {
    if (showResults) return;
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: option,
    }));
  };

  const handleReset = () => {
    setSelectedAnswers({});
    setShowResults(false);
    setCurrentIndex(0);
  };

  const calculateScore = () => {
    let correct = 0;
    questions.forEach((q) => {
      if (selectedAnswers[q.id] === q.correctAnswer) {
        correct++;
      }
    });
    return {
      correct,
      total: questions.length,
      percentage: Math.round((correct / Math.max(1, questions.length)) * 100),
    };
  };

  const scoreStats = calculateScore();

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn pb-12">
      {/* Top Banner */}
      <div className="flex items-center justify-between p-4 rounded-2xl bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/20">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-amber-500/20 text-amber-700 flex items-center justify-center font-bold">
            <Eye className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-amber-900">Faculty Preview Mode</h4>
            <p className="text-xs text-amber-700">
              Interactive test preview of student quiz-taking experience. No submission will be stored.
            </p>
          </div>
        </div>
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 border border-gray-200 rounded-xl shadow-sm transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Editor
        </button>
      </div>

      {/* Quiz Header Card */}
      <div className="p-6 rounded-3xl bg-white border border-gray-100 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <span className="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-100">
              {quiz.status || "Draft"}
            </span>
            <h2 className="text-xl font-bold text-gray-900 mt-2">{quiz.title}</h2>
            {quiz.description && (
              <p className="text-sm text-gray-500 mt-1 max-w-2xl">{quiz.description}</p>
            )}
          </div>

          <div className="flex items-center gap-4 text-xs font-medium text-gray-500">
            <div className="text-center px-4 py-2 rounded-xl bg-gray-50 border border-gray-100">
              <span className="block text-base font-bold text-gray-900">{questions.length}</span>
              Questions
            </div>
            {quiz.passingScore && (
              <div className="text-center px-4 py-2 rounded-xl bg-gray-50 border border-gray-100">
                <span className="block text-base font-bold text-emerald-600">
                  {quiz.passingScore}%
                </span>
                Passing Score
              </div>
            )}
          </div>
        </div>
      </div>

      {questions.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-3xl border border-gray-100 shadow-sm">
          <HelpCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-gray-800">This quiz has no questions yet</h3>
          <p className="text-xs text-gray-500 mt-1 mb-4">Add questions in the editor before previewing.</p>
          <button
            onClick={onBack}
            className="px-5 py-2 text-xs font-semibold text-white bg-emerald-600 rounded-xl hover:bg-emerald-700 transition"
          >
            Go to Editor
          </button>
        </div>
      ) : showResults ? (
        /* Results Card */
        <div className="p-8 rounded-3xl bg-white border border-gray-100 shadow-sm text-center space-y-6">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-emerald-100 text-emerald-600 mx-auto">
            <CheckCircle2 className="w-10 h-10" />
          </div>
          <div>
            <h3 className="text-2xl font-bold text-gray-900">Quiz Completed!</h3>
            <p className="text-sm text-gray-500 mt-1">Here is the simulated score review:</p>
          </div>

          <div className="inline-flex items-center justify-center gap-8 p-6 rounded-2xl bg-gray-50 border border-gray-100">
            <div>
              <span className="block text-3xl font-extrabold text-emerald-600">
                {scoreStats.percentage}%
              </span>
              <span className="text-xs text-gray-500 font-medium">Final Score</span>
            </div>
            <div className="h-10 w-px bg-gray-200" />
            <div>
              <span className="block text-3xl font-extrabold text-gray-900">
                {scoreStats.correct} / {scoreStats.total}
              </span>
              <span className="text-xs text-gray-500 font-medium">Correct Answers</span>
            </div>
          </div>

          <div className="flex items-center justify-center gap-3 pt-2">
            <button
              onClick={handleReset}
              className="flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition"
            >
              <RotateCcw className="w-4 h-4" />
              Retake Preview
            </button>
            <button
              onClick={onBack}
              className="px-6 py-2.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl transition"
            >
              Back to Editor
            </button>
          </div>
        </div>
      ) : (
        /* Interactive Question Card */
        <div className="bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden">
          {/* Question Navigation Tracker */}
          <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-gray-500">
              Question {currentIndex + 1} of {questions.length}
            </span>
            <div className="flex items-center gap-1.5 overflow-x-auto max-w-sm py-1">
              {questions.map((q, idx) => {
                const isAnswered = selectedAnswers[q.id] !== undefined;
                const isCurrent = currentIndex === idx;
                return (
                  <button
                    key={q.id}
                    onClick={() => setCurrentIndex(idx)}
                    className={`w-7 h-7 rounded-lg text-xs font-bold transition-all ${
                      isCurrent
                        ? "bg-emerald-600 text-white ring-2 ring-emerald-600/30"
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
          </div>

          {/* Question Content */}
          <div className="p-8 space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 leading-relaxed">
              {currentQ.questionText}
            </h3>

            {/* Options List */}
            <div className="space-y-3">
              {currentQ.options.map((opt, idx) => {
                const isSelected = selectedAnswers[currentQ.id] === opt;
                const optionLetters = ["A", "B", "C", "D"];
                return (
                  <button
                    key={idx}
                    onClick={() => handleSelectOption(currentQ.id, opt)}
                    className={`w-full p-4 rounded-2xl border text-left flex items-center gap-4 transition-all ${
                      isSelected
                        ? "border-emerald-600 bg-emerald-50/50 ring-2 ring-emerald-600/20 shadow-sm"
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
                    <span className="text-sm text-gray-800 font-medium flex-1">{opt}</span>
                    {isSelected && <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />}
                  </button>
                );
              })}
            </div>

            {/* Explanation Preview Toggle (Faculty special) */}
            {currentQ.explanation && (
              <div className="p-4 rounded-2xl bg-teal-50/60 border border-teal-100 text-xs text-teal-800 flex items-start gap-2.5">
                <Sparkles className="w-4 h-4 text-teal-600 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-teal-900 block mb-0.5">
                    Faculty Key & Explanation:
                  </span>
                  <p>
                    <strong className="text-emerald-700">Correct: {currentQ.correctAnswer}</strong> —{" "}
                    {currentQ.explanation}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Navigation Controls */}
          <div className="px-8 py-4 bg-gray-50/70 border-t border-gray-100 flex items-center justify-between">
            <button
              onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
              disabled={currentIndex === 0}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-gray-600 hover:text-gray-900 disabled:opacity-30 transition"
            >
              <ChevronLeft className="w-4 h-4" /> Previous
            </button>

            <div className="flex items-center gap-3">
              {currentIndex < questions.length - 1 ? (
                <button
                  onClick={() => setCurrentIndex((prev) => Math.min(questions.length - 1, prev + 1))}
                  className="flex items-center gap-1.5 px-5 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl transition shadow-sm"
                >
                  Next <ChevronRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  onClick={() => setShowResults(true)}
                  className="flex items-center gap-2 px-6 py-2 text-xs font-semibold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-xl transition shadow-md shadow-emerald-600/20"
                >
                  Finish Preview
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

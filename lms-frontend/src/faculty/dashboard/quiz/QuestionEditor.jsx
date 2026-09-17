import { useState, useEffect } from "react";
import { X, CheckCircle2, AlertCircle, Save } from "lucide-react";

export default function QuestionEditor({ isOpen, onClose, onSave, question = null, totalQuestions = 0 }) {
  const [questionText, setQuestionText] = useState("");
  const [options, setOptions] = useState(["", "", "", ""]);
  const [correctAnswerIndex, setCorrectAnswerIndex] = useState(0);
  const [explanation, setExplanation] = useState("");
  const [points, setPoints] = useState(1);
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (question) {
      setQuestionText(question.questionText || "");
      const opts = question.options && question.options.length >= 2 
        ? [...question.options] 
        : ["", "", "", ""];
      while (opts.length < 4) opts.push("");
      setOptions(opts);

      const idx = opts.findIndex(o => o === question.correctAnswer);
      setCorrectAnswerIndex(idx >= 0 ? idx : 0);
      setExplanation(question.explanation || "");
      setPoints(question.points || 1);
    } else {
      setQuestionText("");
      setOptions(["", "", "", ""]);
      setCorrectAnswerIndex(0);
      setExplanation("");
      setPoints(1);
    }
    setError("");
  }, [question, isOpen]);

  if (!isOpen) return null;

  const handleOptionChange = (index, value) => {
    const updated = [...options];
    updated[index] = value;
    setOptions(updated);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setError("");

    if (!questionText.trim()) {
      setError("Please enter the question text.");
      return;
    }

    const cleanedOptions = options.map(o => o.trim());
    if (cleanedOptions.some(o => !o)) {
      setError("Please fill in all 4 options.");
      return;
    }

    const uniqueOptions = new Set(cleanedOptions);
    if (uniqueOptions.size !== cleanedOptions.length) {
      setError("All 4 options must be distinct.");
      return;
    }

    const correctAnswer = cleanedOptions[correctAnswerIndex];

    try {
      setIsSaving(true);
      await onSave({
        questionText: questionText.trim(),
        options: cleanedOptions,
        correctAnswer,
        explanation: explanation.trim() || null,
        points: Number(points) || 1,
        order: question ? question.order : totalQuestions
      });
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || "Failed to save question");
    } finally {
      setIsSaving(false);
    }
  };

  const optionLabels = ["A", "B", "C", "D"];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-emerald-50/50 to-teal-50/50">
          <div>
            <h3 className="text-lg font-bold text-gray-900">
              {question ? "Edit Question" : "Add New Question"}
            </h3>
            <p className="text-xs text-gray-500">Multiple choice question with 4 options</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSave} className="flex-1 overflow-y-auto p-6 space-y-5">
          {error && (
            <div className="flex items-center gap-2 p-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Question Text */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
              Question Text *
            </label>
            <textarea
              rows={3}
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              placeholder="e.g. Which of the following is a primary feature of PostgreSQL?"
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm placeholder-gray-400 transition"
              required
            />
          </div>

          {/* Options */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700">
                Answer Options * (Select radio for correct answer)
              </label>
              <span className="text-xs text-emerald-600 font-medium">
                Option {optionLabels[correctAnswerIndex]} selected as correct
              </span>
            </div>

            <div className="space-y-3">
              {options.map((opt, idx) => {
                const isSelected = correctAnswerIndex === idx;
                return (
                  <div
                    key={idx}
                    className={`flex items-center gap-3 p-2.5 rounded-xl border transition-all ${
                      isSelected
                        ? "border-emerald-500 bg-emerald-50/40 ring-1 ring-emerald-500"
                        : "border-gray-200 hover:border-gray-300 bg-white"
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => setCorrectAnswerIndex(idx)}
                      className={`w-8 h-8 rounded-lg font-bold text-xs flex items-center justify-center transition-all ${
                        isSelected
                          ? "bg-emerald-600 text-white shadow-sm"
                          : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                      }`}
                    >
                      {optionLabels[idx]}
                    </button>

                    <input
                      type="text"
                      value={opt}
                      onChange={(e) => handleOptionChange(idx, e.target.value)}
                      placeholder={`Option ${optionLabels[idx]}`}
                      className="flex-1 px-3 py-1.5 text-sm bg-transparent border-none focus:outline-none placeholder-gray-400"
                      required
                    />

                    <button
                      type="button"
                      onClick={() => setCorrectAnswerIndex(idx)}
                      className={`text-xs px-2.5 py-1 rounded-full font-medium transition ${
                        isSelected
                          ? "bg-emerald-100 text-emerald-800 flex items-center gap-1"
                          : "text-gray-400 hover:text-gray-600"
                      }`}
                    >
                      {isSelected ? (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5" /> Correct
                        </>
                      ) : (
                        "Mark Correct"
                      )}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Explanation */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
              Explanation (Optional)
            </label>
            <textarea
              rows={2}
              value={explanation}
              onChange={(e) => setExplanation(e.target.value)}
              placeholder="Explain why this answer is correct to help students learn..."
              className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm placeholder-gray-400 transition"
            />
          </div>

          {/* Points */}
          <div className="w-36">
            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
              Points
            </label>
            <input
              type="number"
              min={1}
              max={10}
              value={points}
              onChange={(e) => setPoints(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-gray-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm"
            />
          </div>
        </form>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100 bg-gray-50/50">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 rounded-xl hover:bg-gray-100 transition"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-5 py-2 text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-sm transition disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {isSaving ? "Saving..." : "Save Question"}
          </button>
        </div>
      </div>
    </div>
  );
}

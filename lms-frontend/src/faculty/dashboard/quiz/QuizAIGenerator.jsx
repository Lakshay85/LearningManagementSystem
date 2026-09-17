import { useState, useEffect } from "react";
import {
  Sparkles,
  X,
  FileText,
  AlertCircle,
  Sliders,
  CheckCircle,
  BookOpen,
  HelpCircle,
  Loader2
} from "lucide-react";
import facultyApi from "../../../utils/facultyApi";
import CustomSelect from "../../../components/common/CustomSelect";

export default function QuizAIGenerator({ isOpen, onClose, onSuccess, initialCourseId = null, courses = [] }) {
  const [selectedCourseId, setSelectedCourseId] = useState(initialCourseId || "");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [topic, setTopic] = useState("");
  const [numQuestions, setNumQuestions] = useState(10);
  const [difficulty, setDifficulty] = useState("medium");
  const [documents, setDocuments] = useState([]);
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  // Update selected course if initialCourseId changes
  useEffect(() => {
    if (initialCourseId) {
      setSelectedCourseId(initialCourseId);
    } else if (courses.length > 0 && !selectedCourseId) {
      setSelectedCourseId(courses[0].id);
    }
  }, [initialCourseId, courses]);

  // Set default title based on selected course
  useEffect(() => {
    if (selectedCourseId && !title) {
      const c = courses.find((x) => x.id === selectedCourseId);
      if (c) {
        setTitle(`${c.title} — AI Assessment`);
      }
    }
  }, [selectedCourseId, courses]);

  // Fetch available documents
  useEffect(() => {
    if (!isOpen) return;
    const fetchDocs = async () => {
      try {
        setLoadingDocs(true);
        const res = await facultyApi.getMyDocuments();
        const docsList = res?.data || res || [];
        setDocuments(docsList);
      } catch (err) {
        console.error("Error fetching documents:", err);
      } finally {
        setLoadingDocs(false);
      }
    };
    fetchDocs();
  }, [isOpen]);

  if (!isOpen) return null;

  const handleDocToggle = (docId) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  const handleSelectAllDocs = () => {
    if (selectedDocIds.length === documents.length) {
      setSelectedDocIds([]);
    } else {
      setSelectedDocIds(documents.map((d) => d.id));
    }
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    setError("");

    if (!selectedCourseId) {
      setError("Please select a course for this quiz.");
      return;
    }

    if (!title.trim()) {
      setError("Please enter a quiz title.");
      return;
    }

    try {
      setGenerating(true);
      const payload = {
        courseId: selectedCourseId,
        title: title.trim(),
        description: description.trim() || null,
        numberOfQuestions: Number(numQuestions),
        difficulty,
        topic: topic.trim() || null,
        documentIds: selectedDocIds.length > 0 ? selectedDocIds : null,
      };

      const res = await facultyApi.generateQuizWithAI(payload);
      const createdQuiz = res?.data || res;
      onSuccess(createdQuiz);
      onClose();
    } catch (err) {
      console.error("AI Generation error:", err);
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Failed to generate quiz. Please verify API configuration."
      );
    } finally {
      setGenerating(false);
    }
  };

  const difficultyLevels = [
    { id: "easy", label: "Easy", desc: "Foundational & definitions", color: "text-emerald-700 bg-emerald-50 border-emerald-200" },
    { id: "medium", label: "Medium", desc: "Concepts & applications", color: "text-amber-700 bg-amber-50 border-amber-200" },
    { id: "hard", label: "Hard", desc: "Complex problem solving", color: "text-rose-700 bg-rose-50 border-rose-200" },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-3xl shadow-2xl border border-gray-100 max-w-2xl w-full max-h-[92vh] flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="relative px-6 py-5 bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-700 text-white overflow-hidden">
          <div className="absolute -right-8 -bottom-8 w-32 h-32 bg-white/10 rounded-full blur-xl pointer-events-none" />
          <div className="flex items-center justify-between relative z-10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center shadow-inner">
                <Sparkles className="w-5 h-5 text-amber-200 animate-pulse" />
              </div>
              <div>
                <h3 className="text-lg font-bold">AI Quiz Generator</h3>
                <p className="text-xs text-emerald-100">
                  Generate grounded multiple-choice questions powered by Groq
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              disabled={generating}
              className="p-1.5 text-white/80 hover:text-white rounded-xl hover:bg-white/10 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleGenerate} className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="flex items-center gap-2 p-3.5 text-sm text-red-700 bg-red-50 border border-red-200 rounded-2xl">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Course Selection */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
              Target Course *
            </label>
            <CustomSelect
              value={selectedCourseId}
              onChange={(e) => setSelectedCourseId(e.target.value)}
              placeholder="Select a course"
              className="bg-white border-gray-200"
              required
            >
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title}
                </option>
              ))}
            </CustomSelect>
          </div>

          {/* Title & Description */}
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
                Quiz Title *
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Chapter 1: Introduction Assessment"
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm placeholder-gray-400"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1.5">
                Topic / Specific Focus (Optional)
              </label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. SQL indexing, transactions, and ACID properties"
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm placeholder-gray-400"
              />
            </div>
          </div>

          {/* Number of Questions Slider */}
          <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-700 flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5 text-emerald-600" />
                Number of Questions
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-600 text-white">
                {numQuestions} questions
              </span>
            </div>
            <input
              type="range"
              min={5}
              max={25}
              step={1}
              value={numQuestions}
              onChange={(e) => setNumQuestions(e.target.value)}
              className="w-full accent-emerald-600 cursor-pointer"
            />
            <div className="flex justify-between text-[11px] text-gray-400 mt-1">
              <span>5 quick check</span>
              <span>10 standard</span>
              <span>15 thorough</span>
              <span>25 comprehensive</span>
            </div>
          </div>

          {/* Difficulty Level */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-2">
              Difficulty Level
            </label>
            <div className="grid grid-cols-3 gap-3">
              {difficultyLevels.map((lvl) => {
                const isSelected = difficulty === lvl.id;
                return (
                  <button
                    key={lvl.id}
                    type="button"
                    onClick={() => setDifficulty(lvl.id)}
                    className={`p-3 rounded-2xl border text-left transition-all ${
                      isSelected
                        ? "border-emerald-500 bg-emerald-50/60 ring-2 ring-emerald-500/20 shadow-sm"
                        : "border-gray-200 hover:border-gray-300 bg-white"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-bold capitalize text-gray-900">{lvl.label}</span>
                      {isSelected && <CheckCircle className="w-4 h-4 text-emerald-600" />}
                    </div>
                    <p className="text-[11px] text-gray-500 line-clamp-1">{lvl.desc}</p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Uploaded Documents Context Picker */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-gray-700 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-teal-600" />
                Reference Uploaded Documents ({selectedDocIds.length} selected)
              </label>
              {documents.length > 0 && (
                <button
                  type="button"
                  onClick={handleSelectAllDocs}
                  className="text-xs text-emerald-600 hover:text-emerald-700 font-medium"
                >
                  {selectedDocIds.length === documents.length ? "Deselect All" : "Select All"}
                </button>
              )}
            </div>

            {loadingDocs ? (
              <div className="p-4 text-center text-xs text-gray-500">Loading documents...</div>
            ) : documents.length === 0 ? (
              <div className="p-4 rounded-2xl bg-amber-50 border border-amber-100 text-xs text-amber-800 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-600" />
                <span>
                  No uploaded course documents found. AI will generate questions based on the course syllabus and topic hints.
                </span>
              </div>
            ) : (
              <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                {documents.map((doc) => {
                  const isChecked = selectedDocIds.includes(doc.id);
                  return (
                    <label
                      key={doc.id}
                      className={`flex items-center gap-3 p-2.5 rounded-xl border cursor-pointer transition ${
                        isChecked
                          ? "border-emerald-500 bg-emerald-50/40"
                          : "border-gray-200 hover:border-gray-300 bg-white"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => handleDocToggle(doc.id)}
                        className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-gray-800 truncate">
                          {doc.title || doc.originalFilename}
                        </p>
                        <p className="text-[10px] text-gray-400 capitalize">
                          {doc.documentType || "Document"} • {(Number(doc.fileSize) / 1024).toFixed(0)} KB
                        </p>
                      </div>
                    </label>
                  );
                })}
              </div>
            )}
          </div>
        </form>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100 bg-gray-50/60">
          <div className="text-xs text-gray-500">
            {generating ? (
              <span className="flex items-center gap-1.5 text-emerald-600 font-medium">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                AI is generating your quiz...
              </span>
            ) : (
              "Questions will be editable before publishing"
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={generating}
              className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 rounded-xl hover:bg-gray-100 transition disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-xl shadow-md shadow-emerald-600/20 transition disabled:opacity-60"
            >
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating Questions...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-amber-200" />
                  Generate Quiz
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

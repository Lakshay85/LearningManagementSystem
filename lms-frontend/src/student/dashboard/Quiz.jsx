import { useState, useEffect } from "react";

const Quiz = () => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);
  const [timeLeft, setTimeLeft] = useState(300); // 5 minutes in seconds

  const questions = [
    {
      id: 1,
      question: "What is the capital of France?",
      options: ["London", "Berlin", "Paris", "Madrid"],
      correct: "Paris",
    },
    {
      id: 2,
      question: "Which planet is known as the Red Planet?",
      options: ["Venus", "Mars", "Jupiter", "Saturn"],
      correct: "Mars",
    },
    {
      id: 3,
      question: "What is 2 + 2?",
      options: ["3", "4", "5", "6"],
      correct: "4",
    },
    {
      id: 4,
      question: "Who wrote 'Romeo and Juliet'?",
      options: ["Shakespeare", "Dickens", "Hemingway", "Tolkien"],
      correct: "Shakespeare",
    },
    {
      id: 5,
      question: "What is the largest ocean on Earth?",
      options: ["Atlantic", "Indian", "Arctic", "Pacific"],
      correct: "Pacific",
    },
  ];

  useEffect(() => {
    if (timeLeft > 0 && !showResults) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timer);
    } else if (timeLeft === 0) {
      setShowResults(true);
    }
  }, [timeLeft, showResults]);

  const handleAnswerSelect = (questionId, answer) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: answer,
    }));
  };

  const handleNext = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const handleSubmit = () => {
    setShowResults(true);
  };

  const calculateScore = () => {
    let score = 0;
    questions.forEach((q) => {
      if (selectedAnswers[q.id] === q.correct) {
        score++;
      }
    });
    return score;
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  if (showResults) {
    const score = calculateScore();
    const percentage = Math.round((score / questions.length) * 100);

    return (
      <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
        <h2 className="text-3xl font-bold text-center mb-6 text-gray-800">
          Quiz Results
        </h2>
        <div className="text-center mb-6">
          <div className="text-6xl font-bold text-blue-600 mb-2">
            {percentage}%
          </div>
          <p className="text-xl text-gray-600">
            You scored {score} out of {questions.length}
          </p>
        </div>
        <div className="space-y-4">
          {questions.map((q, index) => (              <div key={q.id} className="rounded-lg p-4">
              <p className="font-semibold mb-2">
                {index + 1}. {q.question}
              </p>
              <p className="text-sm text-gray-600">
                Your answer:{" "}
                <span
                  className={
                    selectedAnswers[q.id] === q.correct
                      ? "text-green-600 font-semibold"
                      : "text-red-600 font-semibold"
                  }
                >
                  {selectedAnswers[q.id] || "Not answered"}
                </span>
              </p>
              <p className="text-sm text-green-600">
                Correct answer: {q.correct}
              </p>
            </div>
          ))}
        </div>
        <button
          onClick={() => {
            setCurrentQuestion(0);
            setSelectedAnswers({});
            setShowResults(false);
            setTimeLeft(300);
          }}
          className="w-full mt-6 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Retake Quiz
        </button>
      </div>
    );
  }

  const currentQ = questions[currentQuestion];

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Quiz</h2>
        <div className="text-lg font-semibold text-red-600">
          Time: {formatTime(timeLeft)}
        </div>
      </div>

      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>
            Question {currentQuestion + 1} of {questions.length}
          </span>
          <span>
            {Math.round(((currentQuestion + 1) / questions.length) * 100)}%
            Complete
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{
              width: `${((currentQuestion + 1) / questions.length) * 100}%`,
            }}
          ></div>
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-xl font-semibold mb-4 text-gray-800">
          {currentQ.question}
        </h3>
        <div className="space-y-3">
          {currentQ.options.map((option, index) => (
            <label
              key={index}
              className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
            >
              <input
                type="radio"
                name={`question-${currentQ.id}`}
                value={option}
                checked={selectedAnswers[currentQ.id] === option}
                onChange={() => handleAnswerSelect(currentQ.id, option)}
                className="mr-3 text-blue-600"
              />
              <span className="text-gray-700">{option}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="flex justify-between">
        <button
          onClick={handlePrevious}
          disabled={currentQuestion === 0}
          className="px-6 py-2 bg-gray-300 text-gray-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-400 transition-colors"
        >
          Previous
        </button>

        {currentQuestion === questions.length - 1 ? (
          <button
            onClick={handleSubmit}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            Submit Quiz
          </button>
        ) : (
          <button
            onClick={handleNext}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Next
          </button>
        )}
      </div>
    </div>
  );
};

export default Quiz;

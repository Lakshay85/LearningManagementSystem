from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class CreateQuizSchema(BaseModel):
    courseId: str
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    timeLimitMinutes: Optional[int] = None
    passingScore: Optional[int] = Field(None, ge=0, le=100)

class UpdateQuizSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    timeLimitMinutes: Optional[int] = None
    passingScore: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[str] = None

class GenerateQuizSchema(BaseModel):
    courseId: str
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    numberOfQuestions: int = Field(10, ge=1, le=30)
    difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")
    documentIds: Optional[List[str]] = None
    topic: Optional[str] = None
    timeLimitMinutes: Optional[int] = None
    passingScore: Optional[int] = Field(None, ge=0, le=100)

class CreateQuestionSchema(BaseModel):
    questionText: str = Field(..., min_length=1)
    options: List[str] = Field(..., min_items=2, max_items=6)
    correctAnswer: str = Field(..., min_length=1)
    explanation: Optional[str] = None
    order: Optional[int] = 0
    points: Optional[int] = 1

class UpdateQuestionSchema(BaseModel):
    questionText: Optional[str] = None
    options: Optional[List[str]] = None
    correctAnswer: Optional[str] = None
    explanation: Optional[str] = None
    order: Optional[int] = None
    points: Optional[int] = None

class SubmitQuizAnswer(BaseModel):
    questionId: str
    selectedAnswer: str

class SubmitQuizSchema(BaseModel):
    answers: List[SubmitQuizAnswer]

class QuizQuestionResponse(BaseModel):
    id: str
    quizId: str
    questionText: str
    options: List[str]
    correctAnswer: str
    explanation: Optional[str] = None
    order: int
    points: int
    createdAt: Optional[datetime] = None

    class Config:
        from_attributes = True

class QuizQuestionStudentResponse(BaseModel):
    id: str
    quizId: str
    questionText: str
    options: List[str]
    order: int
    points: int

    class Config:
        from_attributes = True

class QuizResponse(BaseModel):
    id: str
    courseId: str
    title: str
    description: Optional[str] = None
    status: str
    timeLimitMinutes: Optional[int] = None
    totalQuestions: int
    passingScore: Optional[int] = None
    createdBy: Optional[str] = None
    publishedAt: Optional[datetime] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True

class QuizDetailResponse(QuizResponse):
    questions: List[QuizQuestionResponse] = []

class StudentQuizDetailResponse(QuizResponse):
    questions: List[QuizQuestionStudentResponse] = []
    hasSubmitted: bool = False
    submission: Optional[Dict[str, Any]] = None

class QuizSubmissionResponse(BaseModel):
    id: str
    quizId: str
    studentId: str
    score: float
    totalCorrect: int
    totalQuestions: int
    answers: List[Dict[str, Any]]
    submittedAt: datetime
    studentName: Optional[str] = None
    studentEmail: Optional[str] = None

    class Config:
        from_attributes = True

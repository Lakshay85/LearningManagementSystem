from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user, RoleChecker
from app.models.enums import QuizStatus
from app.quiz.schemas import (
    CreateQuizSchema, UpdateQuizSchema, GenerateQuizSchema,
    CreateQuestionSchema, UpdateQuestionSchema, SubmitQuizSchema
)
from app.quiz.service import quiz_service

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])

require_faculty_or_admin = RoleChecker(["faculty", "teacher", "admin"])

# ==================== Faculty Endpoints ====================

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_quiz(
    dto: CreateQuizSchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty_or_admin)
):
    """Create a new draft quiz (Faculty)."""
    quiz = await quiz_service.create_quiz(db, current_user["userId"], dto)
    return {
        "success": True,
        "message": "Quiz created successfully",
        "data": quiz
    }

@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_quiz(
    dto: GenerateQuizSchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty_or_admin)
):
    """Generate a quiz with AI from course documents (Faculty)."""
    quiz = await quiz_service.generate_quiz_with_ai(db, current_user["userId"], dto)
    return {
        "success": True,
        "message": f"Generated quiz with {quiz.totalQuestions} questions successfully",
        "data": quiz
    }

@router.get("/course/{courseId}")
async def get_course_quizzes(
    courseId: str,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty_or_admin)
):
    """List all quizzes for a course (Faculty)."""
    quizzes = await quiz_service.get_course_quizzes(db, courseId, status_filter=status)
    return {
        "success": True,
        "data": quizzes
    }

@router.get("/{quizId}")
async def get_quiz(
    quizId: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty_or_admin)
):
    """Get full quiz with questions, correct answers, and explanations (Faculty)."""
    quiz = await quiz_service.get_quiz(db, quizId)
    return {
        "success": True,
        "data": quiz
    }

@router.patch("/{quizId}")
async def update_quiz(
    quizId: str,
    dto: UpdateQuizSchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty_or_admin)
):
    """Update quiz metadata (Faculty)."""
    quiz = await quiz_service.update_quiz(db, quizId, dto)
    return {
        "success": True,
        "message": "Quiz updated successfully",
        "data": quiz
    }

@router.post("/{quizId}/publish")
async def publish_quiz(
    quizId: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty_or_admin)
):
    """Publish a quiz to students (Faculty)."""
    quiz = await quiz_service.publish_quiz(db, quizId)
    return {
        "success": True,
        "message": "Quiz published successfully",
        "data": quiz
    }

@router.post("/{quizId}/archive")
async def archive_quiz(
    quizId: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty_or_admin)
):
    """Archive a quiz (Faculty)."""
    quiz = await quiz_service.archive_quiz(db, quizId)
    return {
        "success": True,
        "message": "Quiz archived successfully",
        "data": quiz
    }

@router.delete("/{quizId}")
async def delete_quiz(
    quizId: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty_or_admin)
):
    """Delete a quiz (Faculty)."""
    await quiz_service.delete_quiz(db, quizId)
    return {
        "success": True,
        "message": "Quiz deleted successfully"
    }

@router.post("/{quizId}/questions", status_code=status.HTTP_201_CREATED)
async def add_question(
    quizId: str,
    dto: CreateQuestionSchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty_or_admin)
):
    """Add a question to a quiz (Faculty)."""
    question = await quiz_service.add_question(db, quizId, dto)
    return {
        "success": True,
        "message": "Question added successfully",
        "data": question
    }

@router.patch("/questions/{questionId}")
async def update_question(
    questionId: str,
    dto: UpdateQuestionSchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty_or_admin)
):
    """Update a quiz question (Faculty)."""
    question = await quiz_service.update_question(db, questionId, dto)
    return {
        "success": True,
        "message": "Question updated successfully",
        "data": question
    }

@router.delete("/questions/{questionId}")
async def delete_question(
    questionId: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty_or_admin)
):
    """Delete a question from a quiz (Faculty)."""
    await quiz_service.delete_question(db, questionId)
    return {
        "success": True,
        "message": "Question deleted successfully"
    }

@router.get("/{quizId}/submissions")
async def get_quiz_submissions(
    quizId: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_faculty_or_admin)
):
    """View all student submissions and results for a quiz (Faculty)."""
    submissions = await quiz_service.get_quiz_submissions(db, quizId)
    return {
        "success": True,
        "data": submissions
    }

# ==================== Student Endpoints ====================

@router.get("/course/{courseId}/published")
async def get_course_published_quizzes(
    courseId: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List published quizzes for an enrolled course (Student)."""
    quizzes = await quiz_service.get_course_quizzes(
        db, courseId, status_filter=QuizStatus.PUBLISHED.value
    )
    
    # Check submission status for each quiz for this student
    quizzes_data = []
    for q in quizzes:
        sub = await quiz_service.get_student_submission(db, str(q.id), current_user["userId"])
        quizzes_data.append({
            "id": str(q.id),
            "courseId": str(q.courseId),
            "title": q.title,
            "description": q.description,
            "status": q.status,
            "timeLimitMinutes": q.timeLimitMinutes,
            "totalQuestions": q.totalQuestions,
            "passingScore": q.passingScore,
            "publishedAt": q.publishedAt.isoformat() if q.publishedAt else None,
            "hasSubmitted": sub is not None,
            "score": sub["score"] if sub else None
        })

    return {
        "success": True,
        "data": quizzes_data
    }

@router.get("/{quizId}/take")
async def get_quiz_for_taking(
    quizId: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get quiz for taking (hides answers if not yet submitted) (Student)."""
    data = await quiz_service.get_quiz_for_student(db, quizId, current_user["userId"])
    return {
        "success": True,
        "data": data
    }

@router.post("/{quizId}/submit")
async def submit_quiz(
    quizId: str,
    dto: SubmitQuizSchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Submit quiz responses (one-time submission per student) (Student)."""
    result = await quiz_service.submit_quiz(db, quizId, current_user["userId"], dto)
    return {
        "success": True,
        "message": "Quiz submitted successfully",
        "data": result
    }

@router.get("/{quizId}/my-result")
async def get_my_quiz_result(
    quizId: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get student's own submission result for a quiz (Student)."""
    submission = await quiz_service.get_student_submission(db, quizId, current_user["userId"])
    if not submission:
        raise HTTPException(status_code=404, detail="No submission found for this quiz")
    return {
        "success": True,
        "data": submission
    }

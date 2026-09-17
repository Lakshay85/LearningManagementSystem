import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update, delete, and_, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.models import Quiz, QuizQuestion, QuizSubmission, Course, CourseEnrollment, User
from app.models.enums import QuizStatus, EnrollmentStatus, UserRole
from app.quiz.schemas import (
    CreateQuizSchema, UpdateQuizSchema, GenerateQuizSchema,
    CreateQuestionSchema, UpdateQuestionSchema, SubmitQuizSchema
)
from app.quiz.ai_generator import quiz_ai_generator
from app.llm.providers import UsageTracker, TokenUsage

logger = logging.getLogger(__name__)

class QuizService:
    async def get_quiz(self, db: AsyncSession, quiz_id: str) -> Quiz:
        """Fetch quiz by ID with questions eager loaded."""
        try:
            q_uuid = UUID(quiz_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid quiz ID format")

        stmt = (
            select(Quiz)
            .where(Quiz.id == q_uuid)
            .options(selectinload(Quiz.questions), selectinload(Quiz.course))
            .execution_options(populate_existing=True)
        )
        res = await db.execute(stmt)
        quiz = res.scalar_one_or_none()
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        return quiz

    async def create_quiz(self, db: AsyncSession, instructor_id: str, dto: CreateQuizSchema) -> Quiz:
        """Create a new blank quiz in draft status."""
        try:
            course_uuid = UUID(dto.courseId)
            user_uuid = UUID(instructor_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")

        # Verify course exists
        course = await db.get(Course, course_uuid)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        quiz = Quiz(
            courseId=course_uuid,
            title=dto.title,
            description=dto.description,
            status=QuizStatus.DRAFT.value,
            timeLimitMinutes=dto.timeLimitMinutes,
            passingScore=dto.passingScore,
            createdBy=user_uuid,
            totalQuestions=0
        )
        db.add(quiz)
        await db.commit()
        await db.refresh(quiz)
        return await self.get_quiz(db, str(quiz.id))

    async def generate_quiz_with_ai(
        self,
        db: AsyncSession,
        instructor_id: str,
        dto: GenerateQuizSchema
    ) -> Quiz:
        """Generate quiz and questions using AI from course materials."""
        try:
            course_uuid = UUID(dto.courseId)
            user_uuid = UUID(instructor_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")

        course = await db.get(Course, course_uuid)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # Check user's LLM quota
        await UsageTracker.check_quota(instructor_id, db)

        # Call AI generator
        questions_data = await quiz_ai_generator.generate_questions(
            course_title=course.title,
            num_questions=dto.numberOfQuestions,
            difficulty=dto.difficulty,
            topic=dto.topic,
            document_ids=dto.documentIds,
            course_id=str(course_uuid)
        )

        # Log LLM usage
        try:
            prompt_tok = dto.numberOfQuestions * 150
            comp_tok = len(questions_data) * 200
            await UsageTracker.log_usage(
                user_id=instructor_id,
                feature="quiz_generation",
                model="qwen/qwen3.8-27b",
                usage=TokenUsage(prompt_tok, comp_tok, prompt_tok + comp_tok),
                db=db
            )
        except Exception as log_err:
            logger.warning(f"Failed to record quiz LLM usage: {log_err}")

        quiz = Quiz(
            courseId=course_uuid,
            title=dto.title,
            description=dto.description,
            status=QuizStatus.DRAFT.value,
            timeLimitMinutes=dto.timeLimitMinutes,
            passingScore=dto.passingScore,
            createdBy=user_uuid,
            totalQuestions=len(questions_data)
        )
        db.add(quiz)
        await db.flush()

        # Add questions
        for idx, q in enumerate(questions_data):
            question = QuizQuestion(
                quizId=quiz.id,
                questionText=q["questionText"],
                options=q["options"],
                correctAnswer=q["correctAnswer"],
                explanation=q.get("explanation"),
                order=idx,
                points=q.get("points", 1)
            )
            db.add(question)

        await db.commit()
        return await self.get_quiz(db, str(quiz.id))

    async def get_course_quizzes(
        self,
        db: AsyncSession,
        course_id: str,
        status_filter: Optional[str] = None
    ) -> List[Quiz]:
        """Fetch all quizzes for a specific course."""
        try:
            course_uuid = UUID(course_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid course ID format")

        conditions = [Quiz.courseId == course_uuid]
        if status_filter:
            conditions.append(Quiz.status == status_filter)

        stmt = (
            select(Quiz)
            .where(and_(*conditions))
            .options(selectinload(Quiz.questions))
            .order_by(desc(Quiz.createdAt))
        )
        res = await db.execute(stmt)
        return res.scalars().all()

    async def update_quiz(
        self,
        db: AsyncSession,
        quiz_id: str,
        dto: UpdateQuizSchema
    ) -> Quiz:
        """Update quiz metadata."""
        quiz = await self.get_quiz(db, quiz_id)
        if dto.title is not None:
            quiz.title = dto.title
        if dto.description is not None:
            quiz.description = dto.description
        if dto.timeLimitMinutes is not None:
            quiz.timeLimitMinutes = dto.timeLimitMinutes
        if dto.passingScore is not None:
            quiz.passingScore = dto.passingScore
        if dto.status is not None:
            quiz.status = dto.status

        await db.commit()
        return await self.get_quiz(db, quiz_id)

    async def publish_quiz(self, db: AsyncSession, quiz_id: str) -> Quiz:
        """Publish quiz so enrolled students can view and take it."""
        quiz = await self.get_quiz(db, quiz_id)
        if not quiz.questions or len(quiz.questions) == 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot publish an empty quiz. Add at least one question."
            )

        quiz.status = QuizStatus.PUBLISHED.value
        quiz.publishedAt = datetime.now()
        quiz.totalQuestions = len(quiz.questions)

        await db.commit()
        return await self.get_quiz(db, quiz_id)

    async def archive_quiz(self, db: AsyncSession, quiz_id: str) -> Quiz:
        """Archive a quiz."""
        quiz = await self.get_quiz(db, quiz_id)
        quiz.status = QuizStatus.ARCHIVED.value
        await db.commit()
        return await self.get_quiz(db, quiz_id)

    async def delete_quiz(self, db: AsyncSession, quiz_id: str) -> bool:
        """Delete a quiz."""
        quiz = await self.get_quiz(db, quiz_id)
        await db.delete(quiz)
        await db.commit()
        return True

    async def add_question(
        self,
        db: AsyncSession,
        quiz_id: str,
        dto: CreateQuestionSchema
    ) -> QuizQuestion:
        """Add a question to a quiz."""
        quiz = await self.get_quiz(db, quiz_id)
        
        # Validate correctAnswer is in options
        if dto.correctAnswer not in dto.options:
            raise HTTPException(
                status_code=400,
                detail="correctAnswer must be one of the provided options"
            )

        order = dto.order if dto.order is not None else len(quiz.questions)
        question = QuizQuestion(
            quizId=quiz.id,
            questionText=dto.questionText,
            options=dto.options,
            correctAnswer=dto.correctAnswer,
            explanation=dto.explanation,
            order=order,
            points=dto.points or 1
        )
        db.add(question)
        quiz.totalQuestions = (quiz.totalQuestions or 0) + 1
        await db.commit()
        await db.refresh(question)
        return question

    async def update_question(
        self,
        db: AsyncSession,
        question_id: str,
        dto: UpdateQuestionSchema
    ) -> QuizQuestion:
        """Edit an existing quiz question."""
        try:
            q_uuid = UUID(question_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid question ID format")

        question = await db.get(QuizQuestion, q_uuid)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        if dto.options is not None:
            question.options = dto.options
        if dto.questionText is not None:
            question.questionText = dto.questionText
        if dto.correctAnswer is not None:
            if question.options and dto.correctAnswer not in question.options:
                raise HTTPException(
                    status_code=400,
                    detail="correctAnswer must be one of the provided options"
                )
            question.correctAnswer = dto.correctAnswer
        if dto.explanation is not None:
            question.explanation = dto.explanation
        if dto.order is not None:
            question.order = dto.order
        if dto.points is not None:
            question.points = dto.points

        await db.commit()
        await db.refresh(question)
        return question

    async def delete_question(self, db: AsyncSession, question_id: str) -> bool:
        """Delete a question from a quiz and reindex remaining questions."""
        try:
            q_uuid = UUID(question_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid question ID format")

        question = await db.get(QuizQuestion, q_uuid)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        quiz_id = question.quizId
        await db.delete(question)

        # Update quiz totalQuestions count
        quiz = await db.get(Quiz, quiz_id)
        if quiz:
            quiz.totalQuestions = max(0, (quiz.totalQuestions or 1) - 1)

        await db.commit()
        return True

    # ==================== Student Taking & Submitting ====================

    async def get_quiz_for_student(
        self,
        db: AsyncSession,
        quiz_id: str,
        student_id: str
    ) -> Dict[str, Any]:
        """
        Fetch quiz details for student taking the quiz.
        Hides correct answers and explanations unless student has already submitted.
        """
        quiz = await self.get_quiz(db, quiz_id)
        
        # Verify student enrollment
        student_uuid = UUID(student_id)
        enrollment_stmt = select(CourseEnrollment).where(
            and_(
                CourseEnrollment.courseId == quiz.courseId,
                CourseEnrollment.studentId == student_uuid,
                CourseEnrollment.status == EnrollmentStatus.ACTIVE
            )
        )
        enrollment_res = await db.execute(enrollment_stmt)
        if not enrollment_res.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="You are not enrolled in this course")

        # Check existing submission
        sub_stmt = select(QuizSubmission).where(
            and_(
                QuizSubmission.quizId == quiz.id,
                QuizSubmission.studentId == student_uuid
            )
        )
        sub_res = await db.execute(sub_stmt)
        submission = sub_res.scalar_one_or_none()

        questions_output = []
        if submission:
            # Student already submitted: show full review
            for q in quiz.questions:
                questions_output.append({
                    "id": str(q.id),
                    "quizId": str(q.quizId),
                    "questionText": q.questionText,
                    "options": q.options,
                    "correctAnswer": q.correctAnswer,
                    "explanation": q.explanation,
                    "order": q.order,
                    "points": q.points
                })
            sub_dict = {
                "id": str(submission.id),
                "score": float(submission.score),
                "totalCorrect": submission.totalCorrect,
                "totalQuestions": submission.totalQuestions,
                "answers": submission.answers,
                "submittedAt": submission.submittedAt.isoformat() if submission.submittedAt else None
            }
        else:
            # Not submitted yet: exclude correctAnswer and explanation
            for q in quiz.questions:
                questions_output.append({
                    "id": str(q.id),
                    "quizId": str(q.quizId),
                    "questionText": q.questionText,
                    "options": q.options,
                    "order": q.order,
                    "points": q.points
                })
            sub_dict = None

        return {
            "id": str(quiz.id),
            "courseId": str(quiz.courseId),
            "title": quiz.title,
            "description": quiz.description,
            "status": quiz.status,
            "timeLimitMinutes": quiz.timeLimitMinutes,
            "totalQuestions": quiz.totalQuestions,
            "passingScore": quiz.passingScore,
            "publishedAt": quiz.publishedAt.isoformat() if quiz.publishedAt else None,
            "createdAt": quiz.createdAt.isoformat() if quiz.createdAt else None,
            "questions": questions_output,
            "hasSubmitted": submission is not None,
            "submission": sub_dict
        }

    async def submit_quiz(
        self,
        db: AsyncSession,
        quiz_id: str,
        student_id: str,
        dto: SubmitQuizSchema
    ) -> Dict[str, Any]:
        """
        Grade answers and record student submission.
        Enforces one submission per student per quiz.
        """
        quiz = await self.get_quiz(db, quiz_id)
        if quiz.status != QuizStatus.PUBLISHED.value:
            raise HTTPException(status_code=400, detail="This quiz is not currently open for submissions")

        student_uuid = UUID(student_id)

        # Check existing submission
        sub_stmt = select(QuizSubmission).where(
            and_(
                QuizSubmission.quizId == quiz.id,
                QuizSubmission.studentId == student_uuid
            )
        )
        existing = (await db.execute(sub_stmt)).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="You have already submitted this quiz")

        # Map questions
        question_map = {str(q.id): q for q in quiz.questions}
        total_questions = len(quiz.questions)
        total_correct = 0
        answers_graded = []

        # Create answer lookup
        submitted_answers = {a.questionId: a.selectedAnswer for a in dto.answers}

        for q in quiz.questions:
            q_id = str(q.id)
            selected = submitted_answers.get(q_id, "")
            is_correct = (selected.strip().lower() == q.correctAnswer.strip().lower()) if selected else False
            if is_correct:
                total_correct += 1

            answers_graded.append({
                "questionId": q_id,
                "questionText": q.questionText,
                "options": q.options,
                "selectedAnswer": selected,
                "correctAnswer": q.correctAnswer,
                "explanation": q.explanation,
                "isCorrect": is_correct,
                "points": q.points if is_correct else 0
            })

        score_percentage = round((total_correct / max(1, total_questions)) * 100, 2)

        submission = QuizSubmission(
            quizId=quiz.id,
            studentId=student_uuid,
            score=score_percentage,
            totalCorrect=total_correct,
            totalQuestions=total_questions,
            answers=answers_graded,
            submittedAt=datetime.now()
        )
        db.add(submission)
        await db.commit()
        await db.refresh(submission)

        return {
            "id": str(submission.id),
            "quizId": str(submission.quizId),
            "studentId": str(submission.studentId),
            "score": float(submission.score),
            "totalCorrect": submission.totalCorrect,
            "totalQuestions": submission.totalQuestions,
            "passed": (score_percentage >= quiz.passingScore) if quiz.passingScore is not None else None,
            "answers": submission.answers,
            "submittedAt": submission.submittedAt.isoformat()
        }

    async def get_quiz_submissions(
        self,
        db: AsyncSession,
        quiz_id: str
    ) -> List[Dict[str, Any]]:
        """Get all student submissions for a quiz (for faculty review)."""
        quiz = await self.get_quiz(db, quiz_id)
        stmt = (
            select(QuizSubmission)
            .where(QuizSubmission.quizId == quiz.id)
            .options(selectinload(QuizSubmission.student))
            .order_by(desc(QuizSubmission.submittedAt))
        )
        res = await db.execute(stmt)
        submissions = res.scalars().all()

        output = []
        for s in submissions:
            student_name = f"{s.student.firstName} {s.student.lastName}" if s.student else "Unknown Student"
            student_email = s.student.email if s.student else ""
            output.append({
                "id": str(s.id),
                "quizId": str(s.quizId),
                "studentId": str(s.studentId),
                "studentName": student_name,
                "studentEmail": student_email,
                "score": float(s.score),
                "totalCorrect": s.totalCorrect,
                "totalQuestions": s.totalQuestions,
                "answers": s.answers,
                "submittedAt": s.submittedAt.isoformat() if s.submittedAt else None
            })
        return output

    async def get_student_submission(
        self,
        db: AsyncSession,
        quiz_id: str,
        student_id: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch a student's own submission for a quiz."""
        try:
            q_uuid = UUID(quiz_id)
            s_uuid = UUID(student_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid ID format")

        stmt = select(QuizSubmission).where(
            and_(
                QuizSubmission.quizId == q_uuid,
                QuizSubmission.studentId == s_uuid
            )
        )
        res = await db.execute(stmt)
        submission = res.scalar_one_or_none()
        if not submission:
            return None

        return {
            "id": str(submission.id),
            "quizId": str(submission.quizId),
            "studentId": str(submission.studentId),
            "score": float(submission.score),
            "totalCorrect": submission.totalCorrect,
            "totalQuestions": submission.totalQuestions,
            "answers": submission.answers,
            "submittedAt": submission.submittedAt.isoformat() if submission.submittedAt else None
        }

quiz_service = QuizService()

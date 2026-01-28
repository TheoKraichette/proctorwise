from typing import Optional, List
from infrastructure.database.models import QuestionModel
from infrastructure.database.mariadb_cluster import SessionLocal
from domain.entities.question import Question
from application.interfaces.question_repository import QuestionRepository


class SQLAlchemyQuestionRepository(QuestionRepository):

    async def create(self, question: Question) -> Question:
        session = SessionLocal()
        try:
            db_question = QuestionModel(
                question_id=question.question_id,
                exam_id=question.exam_id,
                question_number=question.question_number,
                question_type=question.question_type,
                question_text=question.question_text,
                option_a=question.option_a,
                option_b=question.option_b,
                option_c=question.option_c,
                option_d=question.option_d,
                correct_answer=question.correct_answer,
                points=question.points
            )
            session.add(db_question)
            session.commit()
            session.refresh(db_question)
            return self._to_entity(db_question)
        finally:
            session.close()

    async def get_by_id(self, question_id: str) -> Optional[Question]:
        session = SessionLocal()
        try:
            res = session.query(QuestionModel).filter_by(question_id=question_id).first()
            return self._to_entity(res) if res else None
        finally:
            session.close()

    async def get_by_exam(self, exam_id: str) -> List[Question]:
        session = SessionLocal()
        try:
            results = session.query(QuestionModel).filter_by(exam_id=exam_id).order_by(QuestionModel.question_number).all()
            return [self._to_entity(r) for r in results]
        finally:
            session.close()

    async def update(self, question: Question) -> Question:
        session = SessionLocal()
        try:
            db_question = session.query(QuestionModel).filter_by(question_id=question.question_id).first()
            if db_question:
                db_question.question_text = question.question_text
                db_question.option_a = question.option_a
                db_question.option_b = question.option_b
                db_question.option_c = question.option_c
                db_question.option_d = question.option_d
                db_question.correct_answer = question.correct_answer
                db_question.points = question.points
                session.commit()
                session.refresh(db_question)
                return self._to_entity(db_question)
            return None
        finally:
            session.close()

    async def delete(self, question_id: str) -> bool:
        session = SessionLocal()
        try:
            db_question = session.query(QuestionModel).filter_by(question_id=question_id).first()
            if db_question:
                session.delete(db_question)
                session.commit()
                return True
            return False
        finally:
            session.close()

    async def delete_by_exam(self, exam_id: str) -> bool:
        session = SessionLocal()
        try:
            session.query(QuestionModel).filter_by(exam_id=exam_id).delete()
            session.commit()
            return True
        finally:
            session.close()

    def _to_entity(self, db_question: QuestionModel) -> Question:
        return Question(
            question_id=db_question.question_id,
            exam_id=db_question.exam_id,
            question_number=db_question.question_number,
            question_type=db_question.question_type,
            question_text=db_question.question_text,
            option_a=db_question.option_a,
            option_b=db_question.option_b,
            option_c=db_question.option_c,
            option_d=db_question.option_d,
            correct_answer=db_question.correct_answer,
            points=db_question.points,
            created_at=db_question.created_at
        )

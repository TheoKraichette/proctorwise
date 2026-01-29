from typing import Optional, List
import uuid
from infrastructure.database.models import ExamModel, ExamSlotModel
from infrastructure.database.mariadb_cluster import SessionLocal
from domain.entities.exam import Exam
from domain.entities.exam_slot import ExamSlot
from application.interfaces.exam_repository import ExamRepository


class SQLAlchemyExamRepository(ExamRepository):

    async def create(self, exam: Exam) -> Exam:
        session = SessionLocal()
        try:
            db_exam = ExamModel(
                exam_id=exam.exam_id,
                title=exam.title,
                description=exam.description,
                duration_minutes=exam.duration_minutes,
                teacher_id=exam.teacher_id,
                status=exam.status
            )
            session.add(db_exam)
            session.commit()
            session.refresh(db_exam)
            return self._to_entity(db_exam)
        finally:
            session.close()

    async def get_by_id(self, exam_id: str) -> Optional[Exam]:
        session = SessionLocal()
        try:
            res = session.query(ExamModel).filter_by(exam_id=exam_id).first()
            return self._to_entity(res) if res else None
        finally:
            session.close()

    async def get_all(self) -> List[Exam]:
        session = SessionLocal()
        try:
            results = session.query(ExamModel).filter_by(status='active').all()
            return [self._to_entity(r) for r in results]
        finally:
            session.close()

    async def get_by_teacher(self, teacher_id: str) -> List[Exam]:
        session = SessionLocal()
        try:
            results = session.query(ExamModel).filter_by(teacher_id=teacher_id).all()
            return [self._to_entity(r) for r in results]
        finally:
            session.close()

    async def update(self, exam: Exam) -> Exam:
        session = SessionLocal()
        try:
            db_exam = session.query(ExamModel).filter_by(exam_id=exam.exam_id).first()
            if db_exam:
                db_exam.title = exam.title
                db_exam.description = exam.description
                db_exam.duration_minutes = exam.duration_minutes
                db_exam.status = exam.status
                session.commit()
                session.refresh(db_exam)
                return self._to_entity(db_exam)
            return None
        finally:
            session.close()

    async def delete(self, exam_id: str) -> bool:
        session = SessionLocal()
        try:
            db_exam = session.query(ExamModel).filter_by(exam_id=exam_id).first()
            if db_exam:
                db_exam.status = 'deleted'
                session.commit()
                return True
            return False
        finally:
            session.close()

    def _to_entity(self, db_exam: ExamModel) -> Exam:
        return Exam(
            exam_id=db_exam.exam_id,
            title=db_exam.title,
            description=db_exam.description,
            duration_minutes=db_exam.duration_minutes,
            teacher_id=db_exam.teacher_id,
            status=db_exam.status,
            created_at=db_exam.created_at
        )

    # ========== EXAM SLOTS ==========

    async def create_slot(self, exam_id: str, start_time) -> ExamSlot:
        session = SessionLocal()
        try:
            db_slot = ExamSlotModel(
                slot_id=str(uuid.uuid4()),
                exam_id=exam_id,
                start_time=start_time
            )
            session.add(db_slot)
            session.commit()
            session.refresh(db_slot)
            return self._to_slot_entity(db_slot)
        finally:
            session.close()

    async def get_slots_by_exam(self, exam_id: str) -> List[ExamSlot]:
        session = SessionLocal()
        try:
            results = session.query(ExamSlotModel).filter_by(exam_id=exam_id).order_by(ExamSlotModel.start_time).all()
            return [self._to_slot_entity(r) for r in results]
        finally:
            session.close()

    async def delete_slot(self, slot_id: str) -> bool:
        session = SessionLocal()
        try:
            db_slot = session.query(ExamSlotModel).filter_by(slot_id=slot_id).first()
            if db_slot:
                session.delete(db_slot)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def _to_slot_entity(self, db_slot: ExamSlotModel) -> ExamSlot:
        return ExamSlot(
            slot_id=db_slot.slot_id,
            exam_id=db_slot.exam_id,
            start_time=db_slot.start_time,
            created_at=db_slot.created_at
        )

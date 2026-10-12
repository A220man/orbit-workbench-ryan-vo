"""SQLAlchemy entities for SQLite persistence."""
import datetime as dt
import json
import uuid
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from app.core.database import Base


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class DiagramEntity(Base):
    __tablename__ = "diagrams"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(120), nullable=False, index=True)
    diagram_type = Column(String(40), nullable=False, index=True)
    theme = Column(String(40), nullable=False, default="editorial_light")
    content_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    created_by = Column(String(80), nullable=False, default="anonymous")

    @property
    def content(self) -> dict:
        try:
            return json.loads(self.content_json)
        except Exception:
            return {}

    @content.setter
    def content(self, val: dict) -> None:
        self.content_json = json.dumps(val)


class AuditEntity(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    user_id = Column(String(80), nullable=False, index=True)
    action = Column(String(60), nullable=False, index=True)
    resource_type = Column(String(40), nullable=False)
    resource_id = Column(String(64), nullable=False)
    details_json = Column(Text, nullable=False, default="{}")

    @property
    def details(self) -> dict:
        try:
            return json.loads(self.details_json)
        except Exception:
            return {}

    @details.setter
    def details(self, val: dict) -> None:
        self.details_json = json.dumps(val)


class EvaluationRunEntity(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    total_cases = Column(Integer, nullable=False, default=0)
    passed_cases = Column(Integer, nullable=False, default=0)
    accuracy_rate = Column(Float, nullable=False, default=0.0)
    details_json = Column(Text, nullable=False, default="{}")

    @property
    def details(self) -> dict:
        try:
            return json.loads(self.details_json)
        except Exception:
            return {}

    @details.setter
    def details(self, val: dict) -> None:
        self.details_json = json.dumps(val)

import json
from uuid import UUID

from sqlalchemy import DateTime, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import settings
from .contracts import WorkflowRun


class Base(DeclarativeBase):
    pass


class BenchmarkRecord(Base):
    __tablename__ = "benchmark_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    commit_sha: Mapped[str] = mapped_column(String(40), index=True)
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True))


class WorkflowRunRecord(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    original_request: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True))


engine_kwargs = {"pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def create_schema() -> None:
    Base.metadata.create_all(bind=engine)


class SqlRunRepository:
    def save(self, run: WorkflowRun) -> WorkflowRun:
        with SessionLocal() as session:
            record = session.get(WorkflowRunRecord, str(run.id))
            payload = run.model_dump_json()
            if record is None:
                record = WorkflowRunRecord(
                    id=str(run.id),
                    status=run.status.value,
                    original_request=run.original_request,
                    provider=run.provider,
                    model=run.model,
                    payload=payload,
                    created_at=run.created_at,
                )
                session.add(record)
            else:
                record.status = run.status.value
                record.provider = run.provider
                record.model = run.model
                record.payload = payload
            session.commit()
        return run

    def get(self, run_id: UUID) -> WorkflowRun | None:
        with SessionLocal() as session:
            record = session.get(WorkflowRunRecord, str(run_id))
            if record is None:
                return None
            return WorkflowRun.model_validate(json.loads(record.payload))

    def list(self) -> list[WorkflowRun]:
        with SessionLocal() as session:
            records = session.query(WorkflowRunRecord).order_by(WorkflowRunRecord.created_at.desc()).all()
            return [WorkflowRun.model_validate(json.loads(record.payload)) for record in records]

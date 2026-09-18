import json

from .contracts import BenchmarkEvidence
from .database import BenchmarkRecord, SessionLocal
from .repository_evaluation import (
    BENCHMARK_SCENARIO_IDS,
    BENCHMARK_SPECIFICATION_VERSION,
    evaluate_repository_faults,
)


def record_repository_benchmark(commit_sha: str) -> BenchmarkEvidence:
    metrics = evaluate_repository_faults()
    evidence = BenchmarkEvidence(
        commit_sha=commit_sha,
        specification_version=BENCHMARK_SPECIFICATION_VERSION,
        scenario_ids=BENCHMARK_SCENARIO_IDS,
        **metrics.model_dump(),
    )
    with SessionLocal() as session:
        session.add(
            BenchmarkRecord(
                id=str(evidence.id),
                commit_sha=evidence.commit_sha,
                payload=evidence.model_dump_json(),
                created_at=evidence.created_at,
            )
        )
        session.commit()
    return evidence


def list_repository_benchmarks() -> list[BenchmarkEvidence]:
    with SessionLocal() as session:
        records = session.query(BenchmarkRecord).order_by(BenchmarkRecord.created_at.desc()).all()
        return [BenchmarkEvidence.model_validate(json.loads(record.payload)) for record in records]


def detect_benchmark_regression(history: list[BenchmarkEvidence]) -> bool:
    if len(history) < 2:
        return False
    newest, previous = history[0], history[1]
    if newest.specification_version != previous.specification_version or newest.scenario_ids != previous.scenario_ids:
        return True
    return newest.detection_rate < previous.detection_rate or newest.blocking_rate < previous.blocking_rate

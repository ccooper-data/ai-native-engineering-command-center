from app.benchmark_history import detect_benchmark_regression
from app.contracts import BenchmarkEvidence


def benchmark(rate: float) -> BenchmarkEvidence:
    return BenchmarkEvidence(
        commit_sha="a" * 40,
        faults_injected=5,
        faults_detected=int(5 * rate),
        faults_blocked=int(5 * rate),
        detection_rate=rate,
        blocking_rate=rate,
    )


def test_benchmark_regression_detects_lower_control_effectiveness() -> None:
    assert detect_benchmark_regression([benchmark(0.8), benchmark(1.0)]) is True


def test_benchmark_regression_accepts_stable_control_effectiveness() -> None:
    assert detect_benchmark_regression([benchmark(1.0), benchmark(1.0)]) is False


def test_benchmark_regression_requires_history() -> None:
    assert detect_benchmark_regression([benchmark(1.0)]) is False

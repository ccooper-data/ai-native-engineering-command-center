from app.repository_evaluation import evaluate_repository_faults


def test_repository_fault_injection_detects_and_blocks_every_scenario() -> None:
    metrics = evaluate_repository_faults()
    assert metrics.faults_injected == 5
    assert metrics.faults_detected == 5
    assert metrics.faults_blocked == 5
    assert metrics.detection_rate == 1.0
    assert metrics.blocking_rate == 1.0

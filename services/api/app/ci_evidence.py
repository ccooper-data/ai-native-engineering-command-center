from app import contracts

REQUIRED_JOBS = {"backend", "frontend", "security"}


def build_ci_validation(
    run_id: int,
    commit_sha: str,
    jobs: list[dict],
) -> contracts.CIValidationArtifact:
    evidence: list[contracts.CIJobEvidence] = []
    for job in jobs:
        name = str(job["name"])
        conclusion = str(job.get("conclusion") or "unknown")
        checks = [
            str(step["name"])
            for step in job.get("steps", [])
            if step.get("conclusion") == "success"
        ]
        evidence.append(
            contracts.CIJobEvidence(
                name=name,
                conclusion=conclusion,
                passed=conclusion == "success",
                checks=checks,
            )
        )

    by_name = {item.name: item for item in evidence}
    required_present = REQUIRED_JOBS.issubset(by_name)
    required_passed = required_present and all(by_name[name].passed for name in REQUIRED_JOBS)
    return contracts.CIValidationArtifact(
        run_id=run_id,
        commit_sha=commit_sha,
        passed=required_passed,
        jobs=evidence,
    )

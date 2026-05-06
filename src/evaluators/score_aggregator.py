from __future__ import annotations

from src.schemas import HardCheckResult, Rubric, SoftScoreResult


def aggregate_score(soft_scores: list[SoftScoreResult]) -> float:
    scored = [item for item in soft_scores if item.status == "scored" and item.score is not None]
    if not scored:
        return 0.0
    available_weight = sum(item.weight for item in scored)
    if available_weight == 0:
        return 0.0
    weighted = sum(float(item.score) * item.weight for item in scored)
    return round(weighted / available_weight, 2)


def final_decision(
    rubric: Rubric,
    hard_results: list[HardCheckResult],
    soft_scores: list[SoftScoreResult],
    overall_score: float,
) -> tuple[bool, str, str, list[str]]:
    required_hard_failed = [item for item in hard_results if item.required and not item.passed]
    missing_evidence = [item for item in soft_scores if item.status == "insufficient_evidence"]
    pass_score = float(rubric.thresholds.get("pass_score", 3.8))
    auto_accept_score = float(rubric.thresholds.get("auto_accept_score", 4.3))
    review_range = rubric.thresholds.get("human_review_score_range", [3.0, 4.3])

    passed = not required_hard_failed and overall_score >= pass_score
    failure_modes = [item.constraint_id for item in required_hard_failed]
    failure_modes.extend(item.dimension_id for item in soft_scores if item.score is not None and item.score < 3.0)

    if required_hard_failed:
        return False, "Reject", "Fix required hard-constraint failures before release.", failure_modes
    if missing_evidence:
        return passed, "Needs Human Review", "Collect missing evidence or route to a human reviewer.", failure_modes
    if passed and overall_score >= auto_accept_score:
        return True, "Accept", "No immediate action required.", failure_modes
    if review_range[0] <= overall_score <= review_range[1]:
        return passed, "Needs Human Review", "Review borderline quality before using this output.", failure_modes
    if overall_score < pass_score:
        return False, "Reject", "Improve low-scoring dimensions and rerun the eval.", failure_modes
    return passed, "Needs Human Review", "Review result before final decision.", failure_modes

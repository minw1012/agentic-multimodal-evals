from __future__ import annotations

from src.schemas import Rubric


def validate_rubric(rubric: Rubric) -> None:
    if not rubric.rubric_id:
        raise ValueError("rubric_id is required")
    if not rubric.hard_constraints and not rubric.soft_scores:
        raise ValueError("rubric must define hard_constraints or soft_scores")
    total_weight = sum(score.weight for score in rubric.soft_scores)
    if rubric.soft_scores and not 0.99 <= total_weight <= 1.01:
        raise ValueError(f"soft score weights must sum to 1.0, got {total_weight:.3f}")
    if "pass_score" not in rubric.thresholds:
        raise ValueError("thresholds.pass_score is required")

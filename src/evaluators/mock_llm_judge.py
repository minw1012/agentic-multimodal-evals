from __future__ import annotations

from src.schemas import EvidenceBundle, Rubric, SoftScoreResult, TaskSpec


def score_soft_dimensions(rubric: Rubric, task_spec: TaskSpec, evidence_bundle: EvidenceBundle) -> list[SoftScoreResult]:
    return [_score_dimension(score, task_spec, evidence_bundle) for score in rubric.soft_scores]


def _score_dimension(score, task_spec: TaskSpec, evidence_bundle: EvidenceBundle) -> SoftScoreResult:
    image = evidence_bundle.evidence.get("image_analyzer", {})
    ocr = evidence_bundle.evidence.get("ocr", {})
    safety = evidence_bundle.evidence.get("safety_checker", {})
    refs: list[str] = []

    if score.id == "prompt_alignment":
        refs.append("image_analyzer")
        signals = image.get("prompt_alignment_signals", [])
        value = 4.0 + min(len(signals), 2) * 0.5
        explanation = "Image evidence contains prompt-alignment signals." if signals else "Image caption broadly aligns with the prompt."
    elif score.id == "visual_quality":
        refs.append("image_analyzer")
        artifacts = image.get("artifacts", [])
        value = 5.0 if not artifacts else max(2.0, 4.0 - len(artifacts))
        explanation = "No major visual artifacts detected." if not artifacts else f"Visual artifacts detected: {', '.join(artifacts)}."
    elif score.id == "text_rendering":
        refs.append("ocr")
        if not task_spec.required_text:
            return SoftScoreResult(score.id, score.name, None, score.weight, "insufficient_evidence", "No rendered text was requested.", refs)
        value = 5.0 if ocr.get("required_text_present") else 2.0
        explanation = "Required text is legible and exact." if value == 5.0 else "Required text is missing or incorrect."
    elif score.id == "safety":
        refs.append("safety_checker")
        value = 5.0 if safety.get("safe") else 1.0
        explanation = "Safety checker reports low risk." if value == 5.0 else "Safety checker reports policy or safety risk."
    elif score.id == "user_acceptability":
        refs.extend(["image_analyzer", "safety_checker"])
        value = 4.0 if safety.get("safe") and not image.get("artifacts", []) else 3.0
        explanation = "Output appears acceptable based on safety and quality evidence."
    else:
        return SoftScoreResult(score.id, score.name, None, score.weight, "insufficient_evidence", "No mock judge rule exists for this dimension.", refs)

    return SoftScoreResult(
        dimension_id=score.id,
        name=score.name,
        score=min(5.0, max(1.0, value)),
        weight=score.weight,
        status="scored",
        explanation=explanation,
        evidence_refs=refs,
    )

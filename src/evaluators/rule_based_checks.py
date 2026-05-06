from __future__ import annotations

from src.schemas import EvidenceBundle, HardCheckResult, Rubric, TaskSpec


def run_hard_checks(rubric: Rubric, task_spec: TaskSpec, evidence_bundle: EvidenceBundle) -> list[HardCheckResult]:
    results: list[HardCheckResult] = []
    for constraint in rubric.hard_constraints:
        if _should_skip(constraint.condition, task_spec):
            results.append(
                HardCheckResult(
                    constraint_id=constraint.id,
                    name=constraint.name,
                    passed=True,
                    required=constraint.pass_required,
                    skipped=True,
                    explanation="Constraint condition was not met, so the check was skipped.",
                )
            )
            continue

        if constraint.evaluator == "safety_checker":
            result = _check_safety(constraint.id, constraint.name, constraint.pass_required, evidence_bundle)
        elif constraint.evaluator == "ocr":
            result = _check_required_text(constraint.id, constraint.name, constraint.pass_required, task_spec, evidence_bundle)
        elif constraint.evaluator == "image_analyzer":
            result = _check_negative_constraints(constraint.id, constraint.name, constraint.pass_required, task_spec, evidence_bundle)
        else:
            result = HardCheckResult(
                constraint_id=constraint.id,
                name=constraint.name,
                passed=True,
                required=constraint.pass_required,
                skipped=True,
                explanation=f"No rule-based implementation exists for evaluator '{constraint.evaluator}'.",
            )
        results.append(result)
    return results


def _should_skip(condition: str | None, task_spec: TaskSpec) -> bool:
    if not condition:
        return False
    if condition == "prompt.required_text exists":
        return not bool(task_spec.required_text)
    if condition == "prompt.negative_constraints exists":
        return not bool(task_spec.negative_constraints)
    return False


def _check_safety(constraint_id: str, name: str, required: bool, evidence_bundle: EvidenceBundle) -> HardCheckResult:
    safety = evidence_bundle.evidence.get("safety_checker", {})
    passed = bool(safety.get("safe", False))
    flags = safety.get("flags", [])
    explanation = "No safety flags found." if passed else f"Safety flags found: {', '.join(flags)}."
    return HardCheckResult(constraint_id, name, passed, required, False, explanation, ["safety_checker"])


def _check_required_text(
    constraint_id: str,
    name: str,
    required: bool,
    task_spec: TaskSpec,
    evidence_bundle: EvidenceBundle,
) -> HardCheckResult:
    ocr = evidence_bundle.evidence.get("ocr", {})
    expected = task_spec.required_text or ""
    actual = ocr.get("text", "")
    passed = bool(expected and expected.lower() in actual.lower())
    explanation = (
        f"Required text '{expected}' was found in OCR output."
        if passed
        else f"Required text '{expected}' was not found in OCR output '{actual}'."
    )
    return HardCheckResult(constraint_id, name, passed, required, False, explanation, ["ocr"])


def _check_negative_constraints(
    constraint_id: str,
    name: str,
    required: bool,
    task_spec: TaskSpec,
    evidence_bundle: EvidenceBundle,
) -> HardCheckResult:
    image = evidence_bundle.evidence.get("image_analyzer", {})
    objects = {str(item).lower() for item in image.get("objects", [])}
    violations = [constraint for constraint in task_spec.negative_constraints if constraint in objects]
    passed = not violations
    explanation = (
        "No forbidden visual elements detected."
        if passed
        else f"Forbidden visual elements detected: {', '.join(violations)}."
    )
    return HardCheckResult(constraint_id, name, passed, required, False, explanation, ["image_analyzer"])

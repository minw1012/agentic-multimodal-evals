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
            if constraint.id == "required_objects_present":
                result = _check_required_objects(constraint.id, constraint.name, constraint.pass_required, task_spec, evidence_bundle)
            elif constraint.id == "object_count_match":
                result = _check_object_counts(constraint.id, constraint.name, constraint.pass_required, task_spec, evidence_bundle)
            else:
                result = _check_negative_constraints(
                    constraint.id, constraint.name, constraint.pass_required, task_spec, evidence_bundle
                )
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
    if condition == "constraints.expected_objects exists":
        return not bool(task_spec.explicit_constraints.get("expected_objects"))
    if condition == "constraints.expected_object_counts exists":
        return not bool(task_spec.explicit_constraints.get("expected_object_counts"))
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


def _check_required_objects(
    constraint_id: str,
    name: str,
    required: bool,
    task_spec: TaskSpec,
    evidence_bundle: EvidenceBundle,
) -> HardCheckResult:
    image = evidence_bundle.evidence.get("image_analyzer", {})
    expected = [str(item).lower() for item in task_spec.explicit_constraints.get("expected_objects", [])]
    objects = {str(item).lower() for item in image.get("objects", [])}
    missing = [item for item in expected if item not in objects]
    passed = not missing
    explanation = (
        "All required objects were detected."
        if passed
        else f"Missing required objects: {', '.join(missing)}."
    )
    return HardCheckResult(constraint_id, name, passed, required, False, explanation, ["image_analyzer"])


def _check_object_counts(
    constraint_id: str,
    name: str,
    required: bool,
    task_spec: TaskSpec,
    evidence_bundle: EvidenceBundle,
) -> HardCheckResult:
    image = evidence_bundle.evidence.get("image_analyzer", {})
    expected_counts = {
        str(key).lower(): int(value)
        for key, value in task_spec.explicit_constraints.get("expected_object_counts", {}).items()
        if isinstance(value, int) and value >= 0
    }
    actual_counts = _collect_object_counts(image)
    mismatches = []
    for label, expected in expected_counts.items():
        actual = actual_counts.get(label, 0)
        if actual != expected:
            mismatches.append(f"{label}: expected {expected}, got {actual}")
    passed = not mismatches
    explanation = "All object counts matched expected values." if passed else f"Count mismatches: {'; '.join(mismatches)}."
    return HardCheckResult(constraint_id, name, passed, required, False, explanation, ["image_analyzer"])


def _collect_object_counts(image_evidence: dict) -> dict[str, int]:
    detections = image_evidence.get("detections")
    counts: dict[str, int] = {}
    if isinstance(detections, list):
        for item in detections:
            if not isinstance(item, dict):
                continue
            label = str(item.get("class", "")).strip().lower()
            if not label:
                continue
            counts[label] = counts.get(label, 0) + 1
        if counts:
            return counts

    for label in image_evidence.get("objects", []):
        label_str = str(label).strip().lower()
        if not label_str:
            continue
        counts[label_str] = counts.get(label_str, 0) + 1
    return counts

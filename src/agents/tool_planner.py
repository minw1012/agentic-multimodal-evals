from __future__ import annotations

from src.schemas import Rubric, TaskSpec, ToolPlan


def plan_tools(task_spec: TaskSpec, rubric: Rubric) -> ToolPlan:
    tools: list[str] = []
    reasons: dict[str, str] = {}

    if task_spec.output_modality == "image":
        _add(tools, reasons, "image_analyzer", "Image outputs need visual description, object, style, and artifact evidence.")

    evaluator_ids = {constraint.evaluator for constraint in rubric.hard_constraints}
    evaluator_ids.update(score.evaluator for score in rubric.soft_scores)

    if task_spec.required_text or "ocr" in evaluator_ids or "ocr_plus_judge" in evaluator_ids:
        _add(tools, reasons, "ocr", "Prompt or rubric requires rendered text evidence.")

    if "safety_checker" in evaluator_ids:
        _add(tools, reasons, "safety_checker", "Rubric includes safety as a hard constraint.")

    if task_spec.negative_constraints:
        _add(tools, reasons, "image_analyzer", "Negative visual constraints require object evidence.")

    return ToolPlan(tools=tools, reasons=reasons)


def _add(tools: list[str], reasons: dict[str, str], tool_name: str, reason: str) -> None:
    if tool_name not in tools:
        tools.append(tool_name)
    reasons.setdefault(tool_name, reason)

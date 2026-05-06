from __future__ import annotations

import re

from src.schemas import EvalCase, TaskSpec


def parse_intent(eval_case: EvalCase) -> TaskSpec:
    prompt = eval_case.prompt
    required_text = _extract_required_text(prompt)
    negative_constraints = _extract_negative_constraints(prompt)
    explicit_constraints = {
        "required_text": required_text,
        "negative_constraints": negative_constraints,
    }
    if eval_case.eval_spec:
        explicit_constraints.update(eval_case.eval_spec.get("constraints", {}))

    return TaskSpec(
        task_type=eval_case.eval_spec.get("task_type", _infer_task_type(eval_case)),
        output_modality=eval_case.output_modality,
        explicit_constraints=explicit_constraints,
        implicit_expectations=[
            "Output should align with the user's observable intent.",
            "Image should be clear, coherent, and free from major visual artifacts.",
            "If text is requested, rendered text should be legible and exact.",
        ],
        required_text=required_text,
        language=_extract_language(prompt),
        style=_extract_style(prompt),
        mood=_extract_mood(prompt),
        negative_constraints=negative_constraints,
    )


def _infer_task_type(eval_case: EvalCase) -> str:
    if eval_case.output_modality == "image":
        return "image_generation"
    return f"{eval_case.output_modality}_generation"


def _extract_required_text(prompt: str) -> str | None:
    patterns = [
        r'(?:text|words|says|include|write)\s+["“](.+?)["”]',
        r"文本[：:]\s*['\"“](.+?)['\"”]",
        r"写着\s*['\"“](.+?)['\"”]",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_negative_constraints(prompt: str) -> list[str]:
    constraints: list[str] = []
    for match in re.finditer(r"\b(?:no|without|avoid)\s+([^,.]+)", prompt, flags=re.IGNORECASE):
        constraints.append(match.group(1).strip().lower())
    return constraints


def _extract_language(prompt: str) -> str | None:
    lowered = prompt.lower()
    if "chinese" in lowered or "中文" in prompt:
        return "Chinese"
    if "spanish" in lowered:
        return "Spanish"
    if "english" in lowered:
        return "English"
    return None


def _extract_style(prompt: str) -> str | None:
    match = re.search(r"\b(?:in|with)\s+(?:a\s+)?([a-z -]+?)\s+style\b", prompt, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def _extract_mood(prompt: str) -> str | None:
    for mood in ("happy", "calm", "dramatic", "cozy", "minimal", "playful", "serious"):
        if mood in prompt.lower():
            return mood
    return None

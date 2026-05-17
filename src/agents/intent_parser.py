from __future__ import annotations

import json
import os
import re
from urllib import error, request

from src.schemas import EvalCase, TaskSpec


LLM_INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "required_text": {"type": ["string", "null"]},
        "negative_constraints": {"type": "array", "items": {"type": "string"}},
        "language": {"type": ["string", "null"]},
        "style": {"type": ["string", "null"]},
        "mood": {"type": ["string", "null"]},
        "expected_objects": {"type": "array", "items": {"type": "string"}},
        "expected_object_counts": {
            "type": "object",
            "additionalProperties": {"type": "integer", "minimum": 0},
        },
    },
    "additionalProperties": False,
}


def parse_intent(eval_case: EvalCase) -> TaskSpec:
    prompt = eval_case.prompt
    structured = _parse_structured_intent(eval_case)

    required_text = structured.get("required_text") if structured else _extract_required_text(prompt)
    negative_constraints = structured.get("negative_constraints") if structured else _extract_negative_constraints(prompt)
    language = structured.get("language") if structured else _extract_language(prompt)
    style = structured.get("style") if structured else _extract_style(prompt)
    mood = structured.get("mood") if structured else _extract_mood(prompt)
    expected_objects = structured.get("expected_objects") if structured else []
    expected_object_counts = structured.get("expected_object_counts") if structured else {}

    explicit_constraints = {
        "required_text": required_text,
        "negative_constraints": negative_constraints,
        "expected_objects": expected_objects,
        "expected_object_counts": expected_object_counts,
    }
    if eval_case.eval_spec:
        explicit_constraints.update(eval_case.eval_spec.get("constraints", {}))

    return TaskSpec(
        task_type=_resolve_task_type(eval_case),
        output_modality=eval_case.output_modality,
        explicit_constraints=explicit_constraints,
        implicit_expectations=[
            "Output should align with the user's observable intent.",
            "Image should be clear, coherent, and free from major visual artifacts.",
            "If text is requested, rendered text should be legible and exact.",
        ],
        required_text=required_text,
        language=language,
        style=style,
        mood=mood,
        negative_constraints=negative_constraints,
    )


def _resolve_task_type(eval_case: EvalCase) -> str:
    requested = str(eval_case.eval_spec.get("task_type", "image_generation"))
    if requested != "image_generation":
        raise ValueError(f"Only task_type='image_generation' is currently supported, got '{requested}'.")
    if eval_case.output_modality != "image":
        raise ValueError(
            "Only output_modality='image' is currently supported for image_generation task_type."
        )
    return "image_generation"


def _parse_structured_intent(eval_case: EvalCase) -> dict | None:
    from_case = eval_case.eval_spec.get("intent_structured")
    if isinstance(from_case, dict):
        normalized = _normalize_structured_intent(from_case)
        if normalized:
            return normalized

    backend = os.getenv("EVAL_INTENT_PARSER_BACKEND", "auto").strip().lower()
    if backend == "regex":
        return None
    if backend in {"auto", "openai"}:
        parsed = _parse_with_openai(eval_case.prompt)
        if parsed:
            return parsed
    return None


def _parse_with_openai(prompt: str) -> dict | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    model = os.getenv("EVAL_INTENT_MODEL", "gpt-4.1-mini")
    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": (
                    "Extract a structured image-generation intent JSON that follows the provided schema. "
                    "Return only valid JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Prompt:\n"
                    f"{prompt}\n\n"
                    "Schema:\n"
                    f"{json.dumps(LLM_INTENT_SCHEMA)}"
                ),
            },
        ],
        "text": {"format": {"type": "json_object"}},
    }
    req = request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError):
        return None

    text = _extract_response_text(data)
    if not text:
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return _normalize_structured_intent(parsed)


def _extract_response_text(payload: dict) -> str | None:
    output = payload.get("output", [])
    for item in output:
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()
    return payload.get("output_text")


def _normalize_structured_intent(raw: dict) -> dict | None:
    if not isinstance(raw, dict):
        return None

    required_text = _clean_optional_string(raw.get("required_text"))
    language = _clean_optional_string(raw.get("language"))
    style = _clean_optional_string(raw.get("style"))
    mood = _clean_optional_string(raw.get("mood"))
    negative_constraints = _clean_string_list(raw.get("negative_constraints", []), lower=True)
    expected_objects = _clean_string_list(raw.get("expected_objects", []), lower=True)
    expected_object_counts = _clean_nonnegative_int_map(raw.get("expected_object_counts", {}))

    return {
        "required_text": required_text,
        "negative_constraints": negative_constraints,
        "language": language,
        "style": style,
        "mood": mood,
        "expected_objects": expected_objects,
        "expected_object_counts": expected_object_counts,
    }


def _clean_optional_string(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _clean_string_list(value: object, lower: bool = False) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        cleaned = item.strip()
        if not cleaned:
            continue
        items.append(cleaned.lower() if lower else cleaned)
    return items


def _clean_nonnegative_int_map(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    cleaned: dict[str, int] = {}
    for key, count in value.items():
        if not isinstance(key, str):
            continue
        if isinstance(count, bool):
            continue
        if isinstance(count, int) and count >= 0:
            cleaned[key.strip().lower()] = count
    return cleaned


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

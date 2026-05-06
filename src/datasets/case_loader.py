from __future__ import annotations

import json
from pathlib import Path

from src.schemas import EvalCase


def load_case(path: str | Path) -> EvalCase:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return EvalCase(
        case_id=data["case_id"],
        prompt=data["prompt"],
        output_modality=data["output_modality"],
        output=data["output"],
        metadata=data.get("metadata", {}),
        eval_spec=data.get("eval_spec", {}),
        linked_rubric_id=data.get("linked_rubric_id"),
        known_failure_info=data.get("known_failure_info", {}),
    )

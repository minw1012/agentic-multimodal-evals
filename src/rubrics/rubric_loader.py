from __future__ import annotations

import json
from pathlib import Path

from src.schemas import HardConstraint, Rubric, SoftScore


def load_rubric(path: str | Path) -> Rubric:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Rubric(
        rubric_id=data["rubric_id"],
        name=data["name"],
        version=str(data["version"]),
        owner=data["owner"],
        applies_to=data["applies_to"],
        hard_constraints=[HardConstraint(**item) for item in data.get("hard_constraints", [])],
        soft_scores=[SoftScore(**item) for item in data.get("soft_scores", [])],
        thresholds=data.get("thresholds", {}),
        outputs=data.get("outputs", {}),
    )

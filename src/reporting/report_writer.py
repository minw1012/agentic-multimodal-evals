from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from src.schemas import EvalReport


def write_report(report: EvalReport, reports_dir: str | Path = "reports") -> Path:
    output_dir = Path(reports_dir) / report.case_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "result.json"
    output_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
    return output_path

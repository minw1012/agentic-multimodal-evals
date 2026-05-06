from __future__ import annotations

from typing import Protocol

from src.schemas import EvalCase, TaskSpec


class EvidenceTool(Protocol):
    name: str
    version: str

    def run(self, eval_case: EvalCase, task_spec: TaskSpec) -> dict:
        ...

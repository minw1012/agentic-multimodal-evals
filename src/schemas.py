from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvalCase:
    case_id: str
    prompt: str
    output_modality: str
    output: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    eval_spec: dict[str, Any] = field(default_factory=dict)
    linked_rubric_id: str | None = None
    known_failure_info: dict[str, Any] = field(default_factory=dict)


@dataclass
class HardConstraint:
    id: str
    name: str
    description: str
    evaluator: str
    pass_required: bool = True
    condition: str | None = None


@dataclass
class SoftScore:
    id: str
    name: str
    description: str
    evaluator: str
    weight: float
    scale: str = "1-5"


@dataclass
class Rubric:
    rubric_id: str
    name: str
    version: str
    owner: str
    applies_to: dict[str, list[str]]
    hard_constraints: list[HardConstraint]
    soft_scores: list[SoftScore]
    thresholds: dict[str, Any]
    outputs: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskSpec:
    task_type: str
    output_modality: str
    explicit_constraints: dict[str, Any]
    implicit_expectations: list[str]
    required_text: str | None = None
    language: str | None = None
    style: str | None = None
    mood: str | None = None
    negative_constraints: list[str] = field(default_factory=list)


@dataclass
class ToolPlan:
    tools: list[str]
    reasons: dict[str, str]


@dataclass
class EvidenceBundle:
    case_id: str
    modality: str
    evidence: dict[str, Any] = field(default_factory=dict)
    references: list[dict[str, Any]] = field(default_factory=list)
    tool_versions: dict[str, str] = field(default_factory=dict)


@dataclass
class HardCheckResult:
    constraint_id: str
    name: str
    passed: bool
    required: bool
    skipped: bool
    explanation: str
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class SoftScoreResult:
    dimension_id: str
    name: str
    score: float | None
    weight: float
    status: str
    explanation: str
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class EvalReport:
    case_id: str
    passed: bool
    overall_score: float
    recommendation: str
    hard_constraint_results: list[HardCheckResult]
    soft_scores: list[SoftScoreResult]
    failure_modes: list[str]
    recommended_action: str
    evidence: dict[str, Any]
    evidence_references: list[dict[str, Any]]
    rubric_version: str
    judge_version: str
    tool_versions: dict[str, str]
    metadata: dict[str, Any]
